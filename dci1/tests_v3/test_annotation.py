"""Reviewer-workflow tests under amendment A1 (one independent annotator
per model): packet loading, strict blinding, single-annotator enforcement,
autosave/resume, immutable finalisation, incomplete-submission prevention,
exact single-label Gate 1 export compatibility, round-trip preservation,
and researcher diagnostics hidden until the annotator locks."""
from __future__ import annotations

import http.client
import json
import threading
from pathlib import Path

import pytest

from dci1v3.annotation.store import (
    BLINDED_KEYS,
    AnnotationWorkflowError,
    AnnotatorSession,
    diagnostics,
    export_annotations,
    load_packet,
    summary,
)
from dci1v3.annotation.server import AnnotationServer
from dci1v3.analysis.stats import wilson_upper_one_sided
from dci1v3.protocol.constants import GATE1_ANNOTATORS
from dci1v3.verifiers.target import s0_count

REPO_PACKET = Path("/home/cnm13ryan/git/dci/dci1/evidence/dci1-v3/"
                   "gemma-3n-e2b-it/gate1/annotation_packet.jsonl")


def make_packet(path: Path, items: int = 20) -> Path:
    """A fixture packet with the real shape: pass-class rows first."""
    rows = []
    for i in range(items):
        n = (i % 3) + 1
        passes = i < items // 2                     # class-ordered layout
        count = n if passes else n + 1
        response = " ".join(["the plan holds."] + ["however"] * count
                            + ["so the answer stands."])
        rows.append({"item_id": f"prescreen:topic-{i:02d}:solo:A:{n}:0",
                     "constraint_text":
                         f"Use the word however exactly {n} "
                         f"{'time' if n == 1 else 'times'}.",
                     "response_text": response, "n": n})
    path.write_text("".join(
        json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n"
        for r in rows))
    return path


@pytest.fixture()
def packet(tmp_path) -> Path:
    return make_packet(tmp_path / "annotation_packet.jsonl")


@pytest.fixture()
def workspace(tmp_path) -> Path:
    return tmp_path / "annotations"


def session(packet, workspace, annotator="A1") -> AnnotatorSession:
    return AnnotatorSession(packet_path=packet, workspace=workspace,
                            model="gemma-3n-e2b-it", annotator=annotator)


def label_all(s: AnnotatorSession, *, invert: set[int] = frozenset()):
    """Harness labelling by plain reading (test-side truth)."""
    for item in s.payload():
        text = item["response_text"]
        n = int(item["constraint_text"].split("exactly ")[1].split()[0])
        verdict = "pass" if text.split().count("however") == n else "fail"
        if item["display"] in invert:
            verdict = "fail" if verdict == "pass" else "pass"
        s.record(item["display"], label=verdict)


def finalized_annotator(packet, workspace, *, invert=frozenset()):
    s = session(packet, workspace)
    label_all(s, invert=invert)
    s.finalize(face_validity=True)
    return s


# ------------------------------------------------------------- amendment
def test_amendment_single_annotator_constant():
    assert GATE1_ANNOTATORS == 1


# ------------------------------------------------------------- loading
def test_loads_fixture_and_real_packets(packet):
    rows = load_packet(packet)
    assert len(rows) == 20
    assert all({"item_id", "constraint_text", "response_text"} <= set(r)
               for r in rows)
    if REPO_PACKET.exists():                        # read-only, real tree
        real = load_packet(REPO_PACKET)
        assert len(real) >= 150
        assert all(r["constraint_text"].startswith("Use the word however")
                   for r in real)


# ------------------------------------------------------------- blinding
def test_annotator_payload_is_blinded(packet, workspace):
    s = session(packet, workspace)
    payload = s.payload()
    assert len(payload) == 20
    for item in payload:
        assert set(item) == {"display", "constraint_text", "response_text",
                             "label", "flag"}
        for hidden in BLINDED_KEYS:
            assert hidden not in item
    # The packet's class-ordered layout must not survive display ordering.
    order = [s._item_id_for_display(k) for k in range(1, 21)]
    packet_ids = [r["item_id"] for r in load_packet(packet)]
    assert order != packet_ids
    first_half = set(packet_ids[:10])
    leaked = sum(1 for item_id in order[:10] if item_id in first_half)
    assert leaked < 10                              # not class-contiguous


def test_second_annotator_refused(packet, workspace):
    """Amendment A1: exactly one independent annotator per model."""
    session(packet, workspace, "A1").record(1, label="pass")
    with pytest.raises(AnnotationWorkflowError, match="one independent "
                                                      "annotator"):
        session(packet, workspace, "A2")
    resumed = session(packet, workspace, "A1")      # same annotator resumes
    assert resumed.progress()["labelled"] == 1


def test_models_are_independent_workspaces(packet, workspace, tmp_path):
    other_packet = make_packet(tmp_path / "other_packet.jsonl")
    a = session(packet, workspace, "A1")
    b = AnnotatorSession(packet_path=other_packet, workspace=workspace,
                         model="qwen3-4b", annotator="B1")
    a.record(1, label="pass")
    assert b.progress()["labelled"] == 0
    assert b.path != a.path


# ------------------------------------------------------ autosave/resume
def test_autosave_and_resume(packet, workspace):
    first = session(packet, workspace)
    first.record(3, label="pass")
    first.record(4, label="fail", flag=True)
    resumed = session(packet, workspace)             # fresh process/instance
    saved = {i["display"]: i for i in resumed.payload()}
    assert saved[3]["label"] == "pass"
    assert saved[4]["label"] == "fail" and saved[4]["flag"]
    assert resumed.progress()["labelled"] == 2
    assert resumed._item_id_for_display(3) == first._item_id_for_display(3)


def test_packet_change_refused_on_resume(packet, workspace):
    session(packet, workspace).record(1, label="pass")
    packet.write_text(packet.read_text().replace("plan holds", "plan bends"))
    with pytest.raises(AnnotationWorkflowError, match="packet changed"):
        session(packet, workspace)


# --------------------------------------------------------- finalisation
def test_incomplete_submission_prevented(packet, workspace):
    s = session(packet, workspace)
    s.record(1, label="pass")
    s.record(2, flag=True)                           # a flag is not an answer
    with pytest.raises(AnnotationWorkflowError, match="binary label"):
        s.finalize(face_validity=True)
    with pytest.raises(AnnotationWorkflowError, match="one of"):
        s.record(3, label="UNSURE")


def test_finalize_immutable(packet, workspace):
    s = finalized_annotator(packet, workspace)
    with pytest.raises(AnnotationWorkflowError, match="immutable"):
        s.record(1, label="fail")
    with pytest.raises(AnnotationWorkflowError, match="already finalised"):
        s.finalize(face_validity=True)
    assert not (s.path.stat().st_mode & 0o200)       # write bits cleared
    resumed = session(packet, workspace)
    with pytest.raises(AnnotationWorkflowError, match="immutable"):
        resumed.record(1, label="fail")


# --------------------------------------------------------------- export
def test_export_available_after_single_finalisation(packet, workspace):
    s = session(packet, workspace)
    label_all(s)
    with pytest.raises(AnnotationWorkflowError, match="stay hidden"):
        export_annotations(workspace, "gemma-3n-e2b-it", packet)
    s.finalize(face_validity=True)
    out = export_annotations(workspace, "gemma-3n-e2b-it", packet)
    assert out.exists()
    assert summary(workspace, "gemma-3n-e2b-it", packet)["locked"] is True


def test_export_matches_gate1_single_label_contract(packet, workspace):
    finalized_annotator(packet, workspace)
    out = export_annotations(workspace, "gemma-3n-e2b-it", packet)
    annotations = json.loads(out.read_text())
    face = annotations.pop("face_validity")
    assert isinstance(face, list) and len(face) == 1
    assert isinstance(face[0], bool)
    for row in load_packet(packet):
        labels = annotations.get(row["item_id"])     # gate1's exact lookup
        assert labels is not None and len(labels) == 1
        assert labels[0] in ("pass", "fail")
        verifier = ("pass" if s0_count(row["response_text"]) == row["n"]
                    else "fail")
        assert labels[0] == verifier                 # harness labelled truly


def test_round_trip_preserves_ids_and_labels(packet, workspace):
    finalized_annotator(packet, workspace)
    out = export_annotations(workspace, "gemma-3n-e2b-it", packet)
    annotations = json.loads(out.read_text())
    s1 = json.loads((workspace / "gemma-3n-e2b-it" / "A1.json").read_text())
    for item_id, entry in s1["labels"].items():
        assert annotations[item_id] == [entry["label"]]
    packet_ids = {r["item_id"] for r in load_packet(packet)}
    assert set(annotations) - {"face_validity"} == packet_ids


# ---------------------------------------------------------- researcher
def test_diagnostics_hidden_until_locked(packet, workspace):
    s = session(packet, workspace)
    label_all(s)
    report = summary(workspace, "gemma-3n-e2b-it", packet)
    assert report["locked"] is False
    assert report["required_annotators"] == 1
    with pytest.raises(AnnotationWorkflowError, match="stay hidden"):
        diagnostics(workspace, "gemma-3n-e2b-it", packet)
    s.finalize(face_validity=True)
    diag = diagnostics(workspace, "gemma-3n-e2b-it", packet)
    assert diag["items"] == 20 and diag["annotator"] == "A1"
    assert "pairwise_agreement" not in diag          # no inter-annotator view
    assert diag["human_verifier_disagreements"] == 0


def test_diagnostics_disagreement_and_wilson_from_single_labels(
        packet, workspace):
    finalized_annotator(packet, workspace, invert={1, 2})
    diag = diagnostics(workspace, "gemma-3n-e2b-it", packet)
    assert diag["human_verifier_disagreements"] == 2
    by_class = diag["human_vs_verifier_by_class"]
    assert by_class["pass"]["items"] + by_class["fail"]["items"] == 20
    for cls in ("pass", "fail"):
        cell = by_class[cls]
        assert cell["wilson_upper"] == pytest.approx(
            wilson_upper_one_sided(cell["disagreements"], cell["items"]))


# ------------------------------------------------------------- HTTP layer
@pytest.fixture()
def annotator_server(packet, workspace):
    server = AnnotationServer(0, session=session(packet, workspace))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()


def _request(server, method, path, body=None):
    conn = http.client.HTTPConnection("127.0.0.1", server.server_port)
    conn.request(method, path,
                 body=json.dumps(body) if body is not None else None,
                 headers={"Content-Type": "application/json"})
    response = conn.getresponse()
    data = response.read().decode()
    conn.close()
    return response.status, data


def test_http_annotator_flow_is_blinded(annotator_server):
    status, page = _request(annotator_server, "GET", "/")
    assert status == 200
    assert "item_id" not in page and "verifier" not in page.lower()
    status, data = _request(annotator_server, "GET", "/api/items")
    items = json.loads(data)["items"]
    assert status == 200 and len(items) == 20
    for hidden in BLINDED_KEYS:
        assert all(hidden not in item for item in items)
    status, _ = _request(annotator_server, "POST", "/api/label",
                         {"display": 1, "judgment": "SATISFIES"})
    assert status == 200
    status, data = _request(annotator_server, "POST", "/api/label",
                            {"display": 2, "judgment": "UNSURE"})
    assert status == 409 and "SATISFIES or VIOLATES" in data
    status, data = _request(annotator_server, "POST", "/api/finalize",
                            {"face_validity": True})
    assert status == 409                              # incomplete submission


def test_http_dashboard_locks_on_single_finalisation(packet, workspace):
    s = session(packet, workspace, "A1")
    label_all(s)
    server = AnnotationServer(0, session=None, workspace=workspace,
                              packets={"gemma-3n-e2b-it": packet})
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, data = _request(server, "GET", "/api/summary")
        assert status == 200
        model = json.loads(data)["models"][0]
        assert model["locked"] is False
        status, _ = _request(server, "GET",
                             "/api/diagnostics?model=gemma-3n-e2b-it")
        assert status == 409
        status, _ = _request(server, "POST", "/api/export",
                             {"model": "gemma-3n-e2b-it"})
        assert status == 409
        s.finalize(face_validity=True)                # the single annotator
        status, data = _request(server, "GET", "/api/summary")
        assert json.loads(data)["models"][0]["locked"] is True
        status, data = _request(server, "GET",
                                "/api/diagnostics?model=gemma-3n-e2b-it")
        assert status == 200
        assert "pairwise_agreement" not in json.loads(data)
        status, data = _request(server, "POST", "/api/export",
                                {"model": "gemma-3n-e2b-it"})
        assert status == 200
        exported = json.loads(Path(json.loads(data)["path"]).read_text())
        assert all(len(v) == 1 for k, v in exported.items())
    finally:
        server.shutdown()


# ------------------------------------------------------------- residuals
def test_no_active_three_annotator_assumptions_in_source():
    """The amendment leaves no live three-annotator logic in dci1v3."""
    src = Path("/home/cnm13ryan/git/dci/dci1/src/dci1v3")
    offenders = []
    for path in src.rglob("*.py"):
        text = path.read_text()
        if "GATE1_ANNOTATORS = 3" in text or "three annotators" in text \
                or "[label] * 3" in text or "[True, True, True]" in text:
            offenders.append(str(path))
    assert not offenders, offenders
