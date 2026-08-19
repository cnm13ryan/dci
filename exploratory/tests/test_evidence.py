"""Promoted evidence must be complete and reachable, and exports must say what
they are.

`runs/` is gitignored, so the repository's numbers are only checkable to the
extent that something committed carries the rows and the configuration that
produced them. Two failures made that worse than it looked:

  * the run manifests hash files under `runs/` that a clean checkout does not
    have, so nothing they assert can be verified from a clone;
  * the one committed row-level export, `figures/reasoning_compute/data/`, was
    written by a figure path that bypassed the canonical-evidence guard, and
    carried no status at all.

These tests do not require evidence to exist. They require that whatever DOES
exist is self-describing: a promoted bundle that names files it does not carry,
or a derived export with no recoverable producer, is the failure mode.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

EXPLORATORY = Path(__file__).resolve().parents[1]
EVIDENCE = EXPLORATORY / "evidence"

REQUIRED_FIELDS = ("slug", "claim", "promoted_at", "source_run", "code",
                   "design", "model", "seed_regime", "files")


def bundles() -> list[Path]:
    if not EVIDENCE.is_dir():
        return []
    return sorted(p for p in EVIDENCE.iterdir()
                  if p.is_dir() and (p / "evidence.json").exists())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


# ------------------------------------------------------------------ bundles
def test_every_directory_under_evidence_is_a_bundle_or_the_readme():
    """A directory with no `evidence.json` is evidence nobody can interpret."""
    if not EVIDENCE.is_dir():
        pytest.skip("no evidence directory yet")
    orphans = [p.name for p in EVIDENCE.iterdir()
               if p.is_dir() and not (p / "evidence.json").exists()]
    assert not orphans, f"promoted directories without evidence.json: {orphans}"


@pytest.mark.parametrize("bundle", bundles(), ids=lambda p: p.name)
def test_a_bundle_carries_every_required_field(bundle: Path):
    record = json.loads((bundle / "evidence.json").read_text())
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    assert not missing, f"{bundle.name} is missing {missing}"
    assert record["slug"] == bundle.name, "the slug must name its own directory"


@pytest.mark.parametrize("bundle", bundles(), ids=lambda p: p.name)
def test_every_copied_file_is_present_and_matches_its_hash(bundle: Path):
    """The whole point of promotion: the bytes are here, and they are the bytes."""
    record = json.loads((bundle / "evidence.json").read_text())
    for entry in record["files"]:
        if entry.get("status") != "COPIED":
            continue
        path = bundle / entry["file"]
        assert path.exists(), f"{bundle.name} declares {entry['file']} COPIED but it is absent"
        assert sha256(path) == entry["sha256"], (
            f"{bundle.name}/{entry['file']} does not match its recorded hash")


@pytest.mark.parametrize("bundle", bundles(), ids=lambda p: p.name)
def test_a_bundle_carries_the_raw_generations(bundle: Path):
    """Without them the bundle is unverifiable, which defeats promoting it.

    `verify_independently.py` reads `generations.jsonl` unconditionally. A bundle
    that records it ABSENT presents as durable evidence and crashes the moment
    anyone tries to check it — so ABSENT is refused at promotion time, and this
    asserts the property on anything already committed.
    """
    record = json.loads((bundle / "evidence.json").read_text())
    entry = next((f for f in record["files"]
                  if f["file"] == "generations.jsonl"), None)
    assert entry is not None, f"{bundle.name} does not mention generations.jsonl"
    assert entry.get("status") in {"COPIED", "BY_HASH"}, (
        f"{bundle.name} records generations.jsonl as {entry.get('status')}; a "
        "bundle without the raw generations cannot be verified from a clone")


def test_promotion_refuses_a_run_without_raw_generations(tmp_path: Path):
    """The refusal itself, exercised — the tests above only see what got written."""
    import subprocess

    run = tmp_path / "runs" / "stageX_20260101T000000Z"
    run.mkdir(parents=True)
    (run / "config.json").write_text('{"stage":"X","model":{},"selection":{}}')
    (run / "design.jsonl").write_text('{"row_id":"r1"}\n')
    # generations.jsonl deliberately absent

    target = EXPLORATORY / "evidence" / "should-not-exist"
    result = subprocess.run(
        [sys.executable, str(EXPLORATORY / "promote_evidence.py"), str(run),
         "--slug", "should-not-exist", "--claim", "x", "--execute"],
        capture_output=True, text=True, check=False)   # a non-zero exit is the point
    assert result.returncode != 0, "promotion succeeded without raw generations"
    assert "refusing to promote" in result.stderr
    assert not target.exists(), "a bundle was written despite the refusal"


@pytest.mark.parametrize("bundle", bundles(), ids=lambda p: p.name)
def test_a_bundle_records_whether_its_tree_was_dirty(bundle: Path):
    """A bundle built from an uncommitted tree cannot be reconstructed from its
    commit, and that has to be visible rather than inferred."""
    record = json.loads((bundle / "evidence.json").read_text())
    assert "dirty" in record["code"] and "commit" in record["code"]


# ------------------------------------------------------------ derived exports
DERIVED_EXPORT_DIRS = (
    EXPLORATORY / "figures" / "reasoning_compute" / "data",
)


@pytest.mark.parametrize("directory", DERIVED_EXPORT_DIRS,
                         ids=lambda p: str(p.relative_to(EXPLORATORY)))
def test_a_committed_export_directory_names_its_producer(directory: Path):
    """Committed CSVs are read as data; without a producer they are folklore."""
    if not directory.is_dir():
        pytest.skip(f"{directory} is absent")
    provenance = directory / "PROVENANCE.json"
    assert provenance.exists(), (
        f"{directory.relative_to(EXPLORATORY)} holds committed derived data with "
        "no PROVENANCE.json naming the script and run that produced it")
    record = json.loads(provenance.read_text())
    for field in ("produced_by", "regenerate", "source_run_glob", "status"):
        assert field in record, f"PROVENANCE.json is missing {field!r}"


def test_the_superseded_export_still_shows_the_symptom_it_documents():
    """If a regeneration ever lands, this test is what tells us to update the note.

    The recorded symptom is that the committed rows carry the Round 10 transition
    budgets, which the guarded loader cannot produce. Asserting it keeps the
    PROVENANCE note honest in both directions: it fails if the note is stale, and
    it fails if someone regenerates the data without clearing the status.
    """
    pandas = pytest.importorskip("pandas")
    directory = EXPLORATORY / "figures" / "reasoning_compute" / "data"
    rows = directory / "reasoning_rows.csv"
    if not rows.exists():
        pytest.skip("the export is absent")
    record = json.loads((directory / "PROVENANCE.json").read_text())
    if record["status"] != "SUPERSEDED_NOT_REGENERABLE_HERE":
        pytest.skip("the export is no longer marked superseded")
    budgets = set(pandas.read_csv(rows)["reasoning_budget"].unique())
    removed = set(record["expected_after_regeneration"]["removed_budgets"])
    assert removed <= budgets, (
        "the export no longer carries the transition budgets, so it was "
        "regenerated — clear the SUPERSEDED status in PROVENANCE.json")

    # The Round 10 export self-documents its own source in an `experiment`
    # column, which is a sharper symptom than the budget set: the migrated
    # script cannot emit that label at all.
    round10 = directory / "round10_s18.csv"
    if round10.exists():
        labels = set(pandas.read_csv(round10)["experiment"].dropna().unique())
        assert labels == {record["round10_label_before"]}, (
            "round10_s18.csv no longer carries the pre-fix cell label, so it was "
            "regenerated — clear the SUPERSEDED status in PROVENANCE.json")
        assert record["round10_label_after"] not in labels
