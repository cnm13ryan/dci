"""Tests for the human-labelling mechanism that strengthens the
verifier-validation claim: sampling reproducibility and exclusions,
reviewer blindness, append-only record integrity, per-class Wilson
bounds, the sequential stopping rule, abstention handling, and the
protection of registered evidence and the sealed reserved set."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HR = ROOT / "experiments" / "human_review"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HR))

import records_io          # noqa: E402
import sampling            # noqa: E402
import validation          # noqa: E402
from forensics import paths  # noqa: E402

CLASS_TARGETS = {"pass": 52, "fail": 52}


def _load_registered_stats():
    """The registered interval module, loaded by path: the forensics
    workspace never imports the scientific package, so equality of the
    two implementations has to be asserted rather than assumed."""
    path = (paths.REPO / "dci1" / "src" / "dci1v3" / "analysis"
            / "stats.py")
    spec = importlib.util.spec_from_file_location("registered_stats",
                                                  path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_review_dir(tmp_path, ids, components=None):
    """A minimal review directory whose calibration set names real
    population ids, so build_report can resolve verifier truth."""
    components = components or {}
    tmp_path = Path(tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    samples = [{"id": i, "inclusion_probability": 0.1} for i in ids
               if components.get(i, "representative") == "representative"]
    (tmp_path / "calibration_sample.json").write_text(json.dumps(
        {"seed": 1, "samples": samples}))
    boundary = [i for i in ids if components.get(i) == "boundary"]
    if boundary:
        (tmp_path / "extension_batch_1.json").write_text(json.dumps({
            "batch": 1,
            "samples": [{"id": i, "component": "boundary",
                         "boundary_category": "high_n",
                         "inclusion_probability": None}
                        for i in boundary]}))
    return tmp_path


def _write_records(path, rows):
    for row in rows:
        records_io.append_record(path, row)
    return path


@pytest.fixture(scope="module")
def population():
    return sampling.population()


# ------------------------------------------------------ Wilson machinery
def test_wilson_matches_the_registered_implementation():
    registered = _load_registered_stats()
    for trials in (1, 5, 17, 25, 39, 52, 87, 150):
        for errors in range(0, min(trials, 6)):
            assert validation.wilson_upper_one_sided(errors, trials) == \
                pytest.approx(
                    registered.wilson_upper_one_sided(errors, trials),
                    rel=0, abs=1e-15)
            assert validation.wilson_interval(errors, trials) == \
                pytest.approx(registered.wilson_interval(errors, trials))


def test_class_targets_follow_from_the_bound_not_the_other_way():
    # 52 clean labels is the smallest class size meeting 5%; 25 meets 10%
    assert validation.required_n(0, 0.05) == 52
    assert validation.required_n(0, 0.10) == 25
    assert validation.wilson_upper_one_sided(0, 52) <= 0.05
    assert validation.wilson_upper_one_sided(0, 51) > 0.05
    assert validation.wilson_upper_one_sided(0, 25) <= 0.10
    assert validation.wilson_upper_one_sided(0, 24) > 0.10


def test_required_n_grows_with_observed_errors():
    assert validation.required_n(1, 0.05) > validation.required_n(0, 0.05)
    assert validation.required_n(2, 0.05) > validation.required_n(1, 0.05)
    # a rate at or above the target is never reachable by more labelling
    assert validation.reachable_at_observed_rate(1, 52, 0.05) is True
    assert validation.reachable_at_observed_rate(5, 52, 0.05) is False


# --------------------------------------------------------- the sampler
def test_sampling_is_reproducible(population):
    a = sampling.build_extension(1, class_targets=CLASS_TARGETS)
    b = sampling.build_extension(1, class_targets=CLASS_TARGETS)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert a["seed"] == sampling.batch_seed(1)
    assert a["seed"] != sampling.batch_seed(2)


def test_extension_excludes_sealed_calibration_labelled_and_revealed():
    manifest = sampling.build_extension(1, class_targets=CLASS_TARGETS)
    ids = {s["id"] for s in manifest["samples"]}
    assert len(ids) == len(manifest["samples"])          # no duplicates
    assert not ids & sampling.sealed_ids()
    assert not ids & sampling.calibration_ids()
    assert not ids & sampling.labelled_ids()
    assert not ids & sampling.revealed_ids()


def test_extension_reaches_the_per_class_targets(population):
    manifest = sampling.build_extension(1, class_targets=CLASS_TARGETS,
                                        boundary_per_class=8)
    index = {i["id"]: i for i in population}
    rep = [s for s in manifest["samples"]
           if s["component"] == "representative"]
    bnd = [s for s in manifest["samples"] if s["component"] == "boundary"]
    already = sampling.labelled_ids()
    for cls, existing in (("pass", 39), ("fail", 17)):
        assert sum(1 for i in already
                   if index[i]["verifier_class"] == cls) == existing
        drawn = sum(1 for s in rep if s["verifier_class"] == cls)
        assert existing + drawn == CLASS_TARGETS[cls]
        assert sum(1 for s in bnd if s["verifier_class"] == cls) == 8


def test_sample_rows_carry_the_required_provenance(population):
    manifest = sampling.build_extension(1, class_targets=CLASS_TARGETS)
    index = {i["id"]: i for i in population}
    required = {"id", "model", "item_id", "n", "source_pool",
                "response_sha256", "verifier_class", "s0_count",
                "component", "stratum", "inclusion_probability",
                "boundary_category"}
    for row in manifest["samples"]:
        assert required <= set(row)
        assert row["response_sha256"] == \
            index[row["id"]]["response_sha256"]
        if row["component"] == "representative":
            assert 0 < row["inclusion_probability"] <= 1
        else:
            assert row["inclusion_probability"] is None
    assert manifest["sealed_set_sha256"] == sampling.sealed_digest()


def test_sample_response_hashes_bind_to_registered_evidence(population):
    """sha256(raw_response) is the registered content hash, so a human
    record's response hash ties directly to registered evidence."""
    for item in population[:25]:
        pool = __import__("forensics.dataset", fromlist=["x"]).pool_items(
            item["model"])
        text = pool[item["item_id"]]["response_text"]
        assert hashlib.sha256(text.encode()).hexdigest() == \
            item["response_sha256"] == \
            pool[item["item_id"]]["response_hash"]


def test_boundary_categories_are_disjoint_and_declared():
    manifest = sampling.build_extension(1, class_targets=CLASS_TARGETS)
    declared = {c for c, _ in sampling.BOUNDARY_QUOTAS}
    for row in manifest["samples"]:
        if row["component"] == "boundary":
            assert row["boundary_category"] in declared
    assert set(manifest["boundary_pool_sizes"]) >= \
        set(manifest["boundary_realised"])


# ------------------------------------------- evidence and seal protection
def test_sampler_never_writes_registered_evidence_or_the_seal():
    before = {p: p.stat().st_mtime_ns
              for p in paths.EVIDENCE.rglob("*") if p.is_file()}
    sealed_before = sampling.SEALED_PATH.read_bytes()
    sampling.build_extension(1, class_targets=CLASS_TARGETS)
    validation.build_report(
        review_dir=HR,
        record_paths=[HR / "records" / "calibration_Bryan.jsonl"])
    after = {p: p.stat().st_mtime_ns
             for p in paths.EVIDENCE.rglob("*") if p.is_file()}
    assert before == after
    assert sampling.SEALED_PATH.read_bytes() == sealed_before


def test_report_refuses_labels_that_fall_inside_the_sealed_set(tmp_path):
    sealed_id = sorted(sampling.sealed_ids())[0]
    rec = _write_records(tmp_path / "r.jsonl", [
        {"id": sealed_id, "label": "SATISFIES", "annotator": "x",
         "synthetic": False, "set": "s"}])
    review = _fake_review_dir(tmp_path / "rev", [sealed_id])
    with pytest.raises(validation.ValidationError, match="SEALED"):
        validation.build_report(review_dir=review, record_paths=[rec])


# --------------------------------------------------------- the reviewer
def _review_app():
    spec = importlib.util.spec_from_file_location(
        "review_app_hv", HR / "review_app.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["review_app_hv"] = module
    spec.loader.exec_module(module)
    return module


def test_reviewer_display_is_blind_for_every_set():
    app = _review_app()
    forbidden = ("label", "verifier", "effort", "judge", "scout", "s0",
                 "reasoning", "class", "component", "boundary",
                 "probability", "hash")
    for name in app.available_sets():
        items = app.load_items(name)
        assert items
        for item in items:
            assert set(item) == app.DISPLAY_FIELDS
            for key in item:
                assert not any(f in key.lower() for f in forbidden), key


def test_reviewer_refuses_a_sealed_id(tmp_path, monkeypatch):
    app = _review_app()
    sealed_id = sorted(sampling.sealed_ids())[0]
    path = HR / "extension_batch_999.json"
    path.write_text(json.dumps({"batch": 999, "samples": [
        {"id": sealed_id, "component": "representative",
         "boundary_category": None, "inclusion_probability": 0.1}]}))
    try:
        with pytest.raises(SystemExit, match="SEALED"):
            app.load_items("extension999")
    finally:
        path.unlink()


def test_reviewer_never_re_presents_an_item_across_sets(tmp_path,
                                                        monkeypatch):
    app = _review_app()
    already = sorted(sampling.labelled_ids())[:1]
    monkeypatch.setattr(app, "judged_ids", lambda a: set(already))
    monkeypatch.setattr(app, "record_path",
                        lambda s, a: tmp_path / "rec.jsonl")
    items = app.load_items("calibration")
    ids = [i["id"] for i in items]
    assert already[0] in ids                       # it is in the set...
    app.review("calibration", "dup",
               ["S"] * (len(items) - 1))           # ...but not presented
    written = [json.loads(l) for l in
               (tmp_path / "rec.jsonl").read_text().splitlines()]
    assert already[0] not in {r["id"] for r in written}
    assert len(written) == len(items) - 1


# ------------------------------------------------- record integrity
def test_records_are_hash_chained_and_edits_are_detected(tmp_path):
    rec = _write_records(tmp_path / "r.jsonl", [
        {"id": f"m::i{k}", "label": "SATISFIES", "annotator": "a",
         "synthetic": False, "set": "s"} for k in range(3)])
    assert records_io.verify_chain(rec)["chained"] == 3
    lines = rec.read_text().splitlines()
    edited = json.loads(lines[1])
    edited["label"] = "VIOLATES"
    lines[1] = json.dumps(edited, ensure_ascii=False)
    rec.write_text("\n".join(lines) + "\n")
    with pytest.raises(records_io.RecordError, match="record hash"):
        records_io.verify_chain(rec)


def test_deleting_or_reordering_records_breaks_the_chain(tmp_path):
    rec = _write_records(tmp_path / "r.jsonl", [
        {"id": f"m::i{k}", "label": "VIOLATES", "annotator": "a",
         "synthetic": False, "set": "s"} for k in range(3)])
    lines = rec.read_text().splitlines()
    rec.write_text("\n".join([lines[0], lines[2]]) + "\n")
    with pytest.raises(records_io.RecordError, match="chain broken"):
        records_io.verify_chain(rec)


def test_prefix_pins_allow_appends_and_forbid_edits(tmp_path):
    rec = _write_records(tmp_path / "calibration_x.jsonl", [
        {"id": f"m::i{k}", "label": "SATISFIES", "annotator": "a",
         "synthetic": False, "set": "s"} for k in range(2)])
    records_io.pin_records(tmp_path)
    records_io.append_record(rec, {"id": "m::i9", "label": "UNSURE",
                                   "annotator": "a", "synthetic": False,
                                   "set": "s"})
    assert records_io.verify_pins(tmp_path)["pins"] == 1   # append is fine
    lines = rec.read_text().splitlines()
    row = json.loads(lines[0])
    row["label"] = "VIOLATES"
    lines[0] = json.dumps(row, ensure_ascii=False)
    rec.write_text("\n".join(lines) + "\n")
    with pytest.raises(records_io.RecordError, match="pinned prefix"):
        records_io.verify_pins(tmp_path)


def test_legacy_records_are_unchained_but_pinnable(tmp_path):
    """The initial 56 predate chaining: they cannot be retro-chained
    without rewriting them, so a prefix pin is the honest mechanism —
    it detects edits from the moment of pinning onwards."""
    legacy = HR / "records" / "calibration_Bryan.jsonl"
    chain = records_io.verify_chain(legacy)
    assert chain["records"] == 56
    assert chain["unchained_legacy"] == 56
    assert chain["chained"] == 0
    copy = tmp_path / legacy.name
    copy.write_bytes(legacy.read_bytes())
    records_io.pin_records(tmp_path)
    assert records_io.verify_pins(tmp_path)["files"] == 1
    lines = copy.read_text().splitlines()
    row = json.loads(lines[0])
    row["label"] = ("SATISFIES" if row["label"] == "VIOLATES"
                    else "VIOLATES")
    lines[0] = json.dumps(row, ensure_ascii=False)
    copy.write_text("\n".join(lines) + "\n")
    with pytest.raises(records_io.RecordError, match="pinned prefix"):
        records_io.verify_pins(tmp_path)


def test_operational_states_can_never_be_recorded_as_labels(tmp_path):
    for bad in ("invalid_output", "refusal", "generation_failure",
                "truncated", "unscored"):
        with pytest.raises(records_io.RecordError, match="operational"):
            records_io.append_record(tmp_path / "r.jsonl",
                                     {"id": "m::i", "label": bad})
    with pytest.raises(records_io.RecordError, match="vocabulary"):
        records_io.append_record(tmp_path / "r.jsonl",
                                 {"id": "m::i", "label": "MAYBE"})


def test_conflicting_labels_for_one_item_are_refused(tmp_path):
    rec = _write_records(tmp_path / "r.jsonl", [
        {"id": "m::i", "label": "SATISFIES", "annotator": "a",
         "synthetic": False, "set": "s"},
        {"id": "m::i", "label": "VIOLATES", "annotator": "a",
         "synthetic": False, "set": "s"}])
    with pytest.raises(validation.ValidationError, match="conflicting"):
        validation.load_human_records([rec])


def test_synthetic_records_are_refused_as_evidence(tmp_path):
    rec = _write_records(tmp_path / "r.jsonl", [
        {"id": "m::i", "label": "SATISFIES", "annotator": "a",
         "synthetic": True, "set": "s"}])
    with pytest.raises(validation.ValidationError, match="synthetic"):
        validation.load_human_records([rec])
    with pytest.raises(sampling.SamplingError, match="synthetic"):
        sampling.labelled_ids(tmp_path)


# ---------------------------------------------------- report + stopping
def test_report_reproduces_the_current_state_of_the_real_records():
    report = validation.build_report(
        review_dir=HR,
        record_paths=[HR / "records" / "calibration_Bryan.jsonl"])
    assert report["counts"]["labelled"] == 56
    assert report["counts"]["abstentions"] == 0
    assert report["overall_accuracy"] == 1.0
    assert report["table_human_x_verifier"] == {"SATISFIES|pass": 39,
                                                "VIOLATES|fail": 17}
    rep = report["by_component"]["representative"]
    assert (rep["pass"]["cases"], rep["fail"]["cases"]) == (39, 17)
    assert rep["pass"]["meets"]["0.10"] and not rep["pass"]["meets"]["0.05"]
    assert not rep["fail"]["meets"]["0.10"]
    assert rep["pass"]["additional_labels_required"]["0.05"] == 13
    assert rep["fail"]["additional_labels_required"]["0.05"] == 35
    assert report["stopping"]["next_batch_representative_targets"] == \
        {"pass": 13, "fail": 35}
    assert report["stopping"]["decision"] == "CONTINUE"


def test_abstentions_are_counted_and_excluded_from_the_bounds(tmp_path,
                                                              population):
    pass_ids = [i["id"] for i in population
                if i["verifier_class"] == "pass"][:4]
    rows = [{"id": i, "label": "SATISFIES", "annotator": "a",
             "synthetic": False, "set": "s",
             "response_sha256": next(p["response_sha256"]
                                     for p in population if p["id"] == i)}
            for i in pass_ids[:3]]
    rows.append({"id": pass_ids[3], "label": "UNSURE", "annotator": "a",
                 "synthetic": False, "set": "s"})
    rec = _write_records(tmp_path / "r.jsonl", rows)
    review = _fake_review_dir(tmp_path / "rev", pass_ids)
    report = validation.build_report(review_dir=review,
                                     record_paths=[rec])
    assert report["counts"]["records"] == 4
    assert report["counts"]["labelled"] == 3
    assert report["counts"]["abstentions"] == 1
    assert report["counts"]["coverage"] == pytest.approx(0.75)
    assert report["by_component"]["representative"]["pass"]["cases"] == 3
    assert report["operational"]["abstention_ids"] == [pass_ids[3]]


def test_stopping_rule_recomputes_the_requirement_after_a_disagreement(
        tmp_path, population):
    """One disagreement does not leave the original target intact: the
    requirement is recomputed from the observed error count."""
    fails = [i for i in population if i["verifier_class"] == "fail"][:5]
    rows = [{"id": i["id"], "label": "VIOLATES", "annotator": "a",
             "synthetic": False, "set": "s"} for i in fails[:4]]
    rows.append({"id": fails[4]["id"], "label": "SATISFIES",
                 "annotator": "a", "synthetic": False, "set": "s"})
    rec = _write_records(tmp_path / "r.jsonl", rows)
    review = _fake_review_dir(tmp_path / "rev", [i["id"] for i in fails])
    report = validation.build_report(review_dir=review,
                                     record_paths=[rec])
    block = report["by_component"]["representative"]["fail"]
    assert block["cases"] == 5 and block["disagreements"] == 1
    assert block["required_n"]["0.05"] == validation.required_n(1, 0.05)
    assert block["required_n"]["0.05"] > 52          # target moved
    assert report["discordant"][0]["id"] == fails[4]["id"]
    # observed rate 20% cannot meet 5% if it persists
    assert block["reachable_at_observed_rate"]["0.05"] is False
    assert report["stopping"]["decision"] == "ESCALATE"


def test_report_refuses_a_response_hash_that_moved(tmp_path, population):
    item = population[0]
    rec = _write_records(tmp_path / "r.jsonl", [
        {"id": item["id"], "label": "SATISFIES", "annotator": "a",
         "synthetic": False, "set": "s", "response_sha256": "0" * 64}])
    review = _fake_review_dir(tmp_path / "rev", [item["id"]])
    with pytest.raises(validation.ValidationError, match="registered"):
        validation.build_report(review_dir=review, record_paths=[rec])
