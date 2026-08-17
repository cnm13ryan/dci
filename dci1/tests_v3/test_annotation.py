"""Reviewer-workflow tests: packet loading, strict blinding, annotator
independence, autosave/resume, immutable finalisation, incomplete-submission
prevention, exact Gate 1 export compatibility, round-trip preservation, and
locked-only researcher diagnostics."""
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
from dci1v3.protocol.constants import GATE1_ANNOTATORS
from dci1v3.verifiers.target import s0_count

REAL_PACKET = (Path(__file__).resolve().parents[3].parent
               / "gui-staging-nonexistent")  # placeholder, overridden below
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


def test_display_orders_differ_between_annotators(packet, workspace):
    a1 = session(packet, workspace, "A1")
    a2 = session(packet, workspace, "A2")
    order1 = [a1._item_id_for_display(k) for k in range(1, 21)]
    order2 = [a2._item_id_for_display(k) for k in range(1, 21)]
    assert order1 != order2


def test_annotator_independence(packet, workspace):
    a1 = session(packet, workspace, "A1")
    a2 = session(packet, workspace, "A2")
    a2_before = a2.path.read_text()
    a1.record(1, label="pass")
    a1.record(2, label="fail", flag=True)
    assert a2.path.read_text() == a2_before          # A2 file untouched
    assert all(item["label"] is None for item in a2.payload())


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
    make_packet(packet, items=20)                    # rewrite; same size
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
    s = session(packet, workspace)
    label_all(s)
    s.finalize(face_validity=True)
    with pytest.raises(AnnotationWorkflowError, match="immutable"):
        s.record(1, label="fail")
    with pytest.raises(AnnotationWorkflowError, match="already finalised"):
        s.finalize(face_validity=True)
    assert not (s.path.stat().st_mode & 0o200)       # write bits cleared
    resumed = session(packet, workspace)
    with pytest.raises(AnnotationWorkflowError, match="immutable"):
        resumed.record(1, label="fail")


# --------------------------------------------------------------- export
def _three_finalized(packet, workspace, disagree_on=frozenset()):
    for name in ("A1", "A2", "A3"):
        s = session(packet, workspace, name)
        label_all(s, invert=disagree_on if name == "A3" else frozenset())
        s.finalize(face_validity=True)


def test_export_matches_gate1_contract(packet, workspace):
    _three_finalized(packet, workspace)
    out = export_annotations(workspace, "gemma-3n-e2b-it", packet)
    annotations = json.loads(out.read_text())
    face = annotations.pop("face_validity")
    assert isinstance(face, list) and len(face) == GATE1_ANNOTATORS
    assert all(isinstance(f, bool) for f in face)
    for row in load_packet(packet):
        labels = annotations.get(row["item_id"])     # gate1's exact lookup
        assert labels is not None and len(labels) == GATE1_ANNOTATORS
        assert all(label in ("pass", "fail") for label in labels)
        majority = ("pass" if sum(1 for l in labels if l == "pass") >= 2
                    else "fail")                     # gate1's majority rule
        verifier = ("pass" if s0_count(row["response_text"]) == row["n"]
                    else "fail")
        assert majority == verifier                  # harness labelled truly


def test_round_trip_preserves_ids_and_labels(packet, workspace):
    _three_finalized(packet, workspace)
    out = export_annotations(workspace, "gemma-3n-e2b-it", packet)
    annotations = json.loads(out.read_text())
    s1 = json.loads((workspace / "gemma-3n-e2b-it" / "A1.json").read_text())
    for item_id, entry in s1["labels"].items():
        assert annotations[item_id][0] == entry["label"]
    packet_ids = {r["item_id"] for r in load_packet(packet)}
    assert set(annotations) - {"face_validity"} == packet_ids


def test_export_refused_before_lock(packet, workspace):
    for name in ("A1", "A2"):
        s = session(packet, workspace, name)
        label_all(s)
        s.finalize(face_validity=True)
    with pytest.raises(AnnotationWorkflowError, match="stay hidden|"
                                                      "annotators finalised"):
        export_annotations(workspace, "gemma-3n-e2b-it", packet)


# ---------------------------------------------------------- researcher
def test_diagnostics_hidden_until_locked(packet, workspace):
    a1 = session(packet, workspace, "A1")
    label_all(a1)
    a1.finalize(face_validity=True)
    report = summary(workspace, "gemma-3n-e2b-it", packet)
    assert report["locked"] is False
    assert {"agreement", "verifier", "majority"}.isdisjoint(
        {k.split("_")[0] for s in report["sessions"] for k in s})
    with pytest.raises(AnnotationWorkflowError, match="stay hidden"):
        diagnostics(workspace, "gemma-3n-e2b-it", packet)
    for name in ("A2", "A3"):
        s = session(packet, workspace, name)
        label_all(s, invert={1, 2} if name == "A3" else frozenset())
        s.finalize(face_validity=True)
    diag = diagnostics(workspace, "gemma-3n-e2b-it", packet)
    assert diag["items"] == 20
    assert diag["pairwise_agreement"]["A1|A2"] == 1.0
    assert diag["pairwise_agreement"]["A1|A3"] == 0.9
    assert diag["majority_verifier_disagreements"] == 0   # majority robust


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


def test_http_dashboard_hides_diagnostics_until_locked(packet, workspace):
    a1 = session(packet, workspace, "A1")
    label_all(a1)
    a1.finalize(face_validity=True)
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
    finally:
        server.shutdown()
