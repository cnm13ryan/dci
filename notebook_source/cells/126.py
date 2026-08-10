class CacheIntegrityError(RuntimeError):
    """Raised when the journal cannot be trusted to represent the design."""


class FrozenPlanMismatch(RuntimeError):
    """Raised when an existing frozen artefact disagrees with the current one."""


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not Path(path).exists():
        return []
    records, text = [], Path(path).read_text(encoding="utf-8")
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise CacheIntegrityError(
                f"malformed JSON at line {n} of {path}. Batch payloads are "
                "written atomically, so a malformed line means the file was "
                "edited or the storage is damaged.") from exc
    return records


def atomic_write(path: Path, text: str) -> None:
    """Atomic within one filesystem: write a sibling temp file, then rename."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def durable_write(path: Path, text: str, verify: Optional[bool] = None) -> None:
    """Write into the durable root and read back to prove the bytes landed.

    A mounted network filesystem can accept a write and lose it. Verification is
    cheap relative to regenerating a batch.
    """
    verify = CFG.verify_drive_mirror if verify is None else verify
    atomic_write(path, text)
    if verify:
        expected = sha_text(text)
        for _ in range(2):
            if Path(path).exists() and sha_file(path) == expected:
                return
            time.sleep(0.2)
            atomic_write(path, text)
        raise IOError(
            f"durable write to {path} could not be verified. The durable root "
            "may be full or disconnected; stopping rather than continuing with "
            "an unverified journal.")


def local_stage_dir(stage: str) -> Path:
    d = CACHE_DIR / "responses" / stage
    d.mkdir(parents=True, exist_ok=True)
    return d


def durable_stage_dir(stage: str) -> Path:
    d = RESPONSE_DIR / stage
    d.mkdir(parents=True, exist_ok=True)
    return d


def quarantine(path: Path, stage: str, reason: str) -> None:
    target_dir = QUARANTINE_DIR / stage
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / path.name
    try:
        shutil.copy2(path, target)
        path.unlink()
    except Exception:
        pass
    (target_dir / (path.name + ".reason.txt")).write_text(
        f"{datetime.now(timezone.utc).isoformat()}\n{reason}\n", encoding="utf-8")


def _manifest_is_valid(manifest: dict[str, Any], plan_by_index: dict[int, dict],
                       body_path: Path) -> tuple[bool, str]:
    planned = plan_by_index.get(manifest.get("planned_batch_index"))
    if planned is None:
        return False, "batch index is not in the current batch plan"
    if planned["row_ids"] != manifest.get("row_ids_planned"):
        return False, "planned row ids differ from the current batch plan"
    if manifest.get("execution_sha256") != EXECUTION_SHA256:
        return False, (f"execution fingerprint {manifest.get('execution_sha256', '')[:12]} "
                       f"does not match {EXECUTION_SHA256[:12]}")
    for key in ("tokenizer_sha256", "chat_template_sha256"):
        expected = TOKENIZER_STATE.get(key)
        if expected is not None and manifest.get(key) not in (None, expected):
            return False, f"{key} differs from the loaded tokenizer"
    if not body_path.exists():
        return False, "payload file is absent"
    if sha_file(body_path) != manifest.get("content_sha256"):
        return False, "payload hash does not match the commit manifest"
    return True, ""


def restore_from_drive(stage: str, plan: list[dict[str, Any]]) -> dict[str, int]:
    """Rebuild the local fast cache from the durable mirror.

    Only fully verified batches are restored. Anything else is quarantined with
    a written reason, so a corrupted or foreign batch is visible rather than
    silently regenerated or silently trusted.
    """
    stats = {"examined": 0, "restored": 0, "already_local": 0, "quarantined": 0,
             "rows_restored": 0}
    durable, local = durable_stage_dir(stage), local_stage_dir(stage)
    plan_by_index = {b["batch_index"]: b for b in plan}

    with phase("drive_restore"):
        for commit_path in sorted(durable.glob("batch-*.commit.json")):
            stats["examined"] += 1
            try:
                manifest = json.loads(commit_path.read_text())
            except json.JSONDecodeError:
                quarantine(commit_path, stage, "commit marker is not valid JSON")
                stats["quarantined"] += 1
                continue
            body_path = durable / manifest.get("payload_file", "")
            ok, reason = _manifest_is_valid(manifest, plan_by_index, body_path)
            if not ok:
                quarantine(commit_path, stage, reason)
                if body_path.exists():
                    quarantine(body_path, stage, reason)
                stats["quarantined"] += 1
                continue
            local_commit = local / commit_path.name
            local_body = local / body_path.name
            if local_commit.exists() and local_body.exists() and \
                    sha_file(local_body) == manifest["content_sha256"]:
                stats["already_local"] += 1
                continue
            shutil.copy2(body_path, local_body)
            shutil.copy2(commit_path, local_commit)
            stats["restored"] += 1
            stats["rows_restored"] += len(manifest.get("row_ids_planned", []))
    return stats


def commit_batch(stage: str, planned_index: int, attempt: int,
                 payload: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
    """Payload first, then the commit marker, locally and then durably.

    A crash between the two leaves an uncommitted payload that resume ignores,
    so a planned batch is either wholly present and trusted or wholly absent.
    """
    local, durable = local_stage_dir(stage), durable_stage_dir(stage)
    payload_name = f"batch-{planned_index:06d}-attempt-{attempt:02d}.jsonl"
    commit_name = f"batch-{planned_index:06d}.commit.json"
    body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in payload)
    manifest = {**manifest, **row_fingerprint(),
                "payload_file": payload_name,
                "content_sha256": sha_text(body),
                "status": "complete",
                "model_profile": CFG.model_profile,
                "committed_utc": datetime.now(timezone.utc).isoformat()}
    marker = json.dumps(manifest, indent=2, default=str)

    atomic_write(local / payload_name, body)
    atomic_write(local / commit_name, marker)
    if CFG.mirror_committed_batches:
        with phase("drive_mirror"):
            durable_write(durable / payload_name, body)
            durable_write(durable / commit_name, marker)


CACHE_STATS: dict[str, dict[str, int]] = {}


def read_commits(stage: str, plan: list[dict[str, Any]]) -> tuple[dict[str, dict], dict]:
    """Read the LOCAL cache only. Restoration is an explicit, prior step."""
    d = local_stage_dir(stage)
    plan_by_index = {b["batch_index"]: b for b in plan}
    payload: dict[str, dict] = {}
    audit = {"committed": 0, "rejected_plan": 0, "rejected_context": 0,
             "rejected_content": 0, "quarantined": 0, "duplicate": 0}

    for commit_path in sorted(d.glob("batch-*.commit.json")):
        try:
            manifest = json.loads(commit_path.read_text())
        except json.JSONDecodeError:
            audit["quarantined"] += 1
            quarantine(commit_path, stage, "local commit marker is not valid JSON")
            continue
        body_path = d / manifest.get("payload_file", "")
        ok, reason = _manifest_is_valid(manifest, plan_by_index, body_path)
        if not ok:
            if "batch plan" in reason:
                audit["rejected_plan"] += 1
            elif "fingerprint" in reason or "tokenizer" in reason or "template" in reason:
                audit["rejected_context"] += 1
            else:
                audit["rejected_content"] += 1
            continue
        for record in load_jsonl(body_path):
            if record["row_id"] in payload:
                audit["duplicate"] += 1
                continue
            payload[record["row_id"]] = record
        audit["committed"] += 1
    return payload, audit


print("Durable storage layer ready. Restore verifies payload hash, execution "
      "fingerprint, tokenizer and chat-template hashes, and batch-plan "
      "membership before anything enters the local cache.")
