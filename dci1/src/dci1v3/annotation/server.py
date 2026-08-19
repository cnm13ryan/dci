"""Local reviewer GUI: a stdlib HTTP server, no dependencies.

Annotator mode serves exactly one blinded (model, annotator) session:

    python -m dci1v3.annotation.server --model gemma-3n-e2b-it \\
        --annotator A1 [--port 8765]

Under amendment A1, exactly one independent annotator covers each model
packet. Researcher mode serves the progress dashboard (and, only once that
annotator has irrevocably finalised, human-to-verifier diagnostics +
export):

    python -m dci1v3.annotation.server --dashboard [--port 8766]

The server binds to 127.0.0.1 only. Annotator payloads carry no item
identities, verifier information, or sampling status; judgments autosave
on every keypress.
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from dci1v3.annotation import INTERFACE_VERSION
from dci1v3.annotation import rubric
from dci1v3.annotation.store import (
    AnnotationWorkflowError,
    AnnotatorSession,
    diagnostics,
    export_annotations,
    summary,
)

JUDGMENTS = {"SATISFIES": "pass", "VIOLATES": "fail"}

_BASE_CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { margin: 0; font: 16px/1.55 system-ui, sans-serif; color: #1a202c;
       background: #f4f5f7; }
main { max-width: 46rem; margin: 0 auto; padding: 2rem 1.25rem 4rem; }
h1 { font-size: 1.25rem; } h2 { font-size: 1.05rem; }
.card { background: #fff; border: 1px solid #dcdfe4; border-radius: 8px;
        padding: 1.1rem 1.3rem; margin: 0.9rem 0; }
.rule { font-weight: 600; }
.resp { white-space: pre-wrap; font-family: ui-monospace, monospace;
        font-size: 0.95rem; background: #fafbfc; border: 1px solid #e4e7eb;
        border-radius: 6px; padding: 0.9rem 1rem; min-height: 5rem; }
.bar { display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap;
       margin: 0.8rem 0; }
button { font: inherit; padding: 0.45rem 1.0rem; border-radius: 6px;
         border: 1px solid #c3c8cf; background: #fff; cursor: pointer; }
button.primary { background: #1f6f43; border-color: #1f6f43; color: #fff; }
button.danger  { background: #8f2f2f; border-color: #8f2f2f; color: #fff; }
button:disabled { opacity: 0.45; cursor: default; }
.key { display: inline-block; border: 1px solid #b9bec6; border-bottom-width:
       2px; border-radius: 4px; padding: 0 0.4rem; font-family: ui-monospace,
       monospace; background: #fff; }
.sel { outline: 3px solid #1f6f43; }
.sel-v { outline: 3px solid #8f2f2f; }
.muted { color: #5a6472; font-size: 0.9rem; }
.flagged { color: #8a6d1a; font-weight: 600; }
.banner { background: #eef6f0; border: 1px solid #bcd8c4; border-radius: 6px;
          padding: 0.7rem 1rem; }
table { border-collapse: collapse; width: 100%; }
td, th { border: 1px solid #dcdfe4; padding: 0.4rem 0.6rem;
         text-align: left; font-size: 0.92rem; }
a.jump { cursor: pointer; text-decoration: underline; margin-right: 0.4rem; }
"""

_ANNOTATOR_HTML = """<!doctype html>
<meta charset="utf-8">
<title>Gate 1 annotation</title>
<style>%(css)s</style>
<main id="app"></main>
<script>
const RUBRIC = %(rubric)s;
let items = [], progress = {}, idx = 0, view = "instructions";
const app = document.getElementById("app");

function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {}))
    if (k === "onclick") node.onclick = v; else node.setAttribute(k, v);
  for (const c of children)
    node.append(typeof c === "string" ? document.createTextNode(c) : c);
  return node;
}

async function api(path, body) {
  const opts = body === undefined ? {} :
    {method: "POST", headers: {"Content-Type": "application/json"},
     body: JSON.stringify(body)};
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) { alert(data.error || "request failed"); throw data; }
  return data;
}

async function refresh() {
  const data = await api("/api/items");
  items = data.items; progress = data.progress;
}

function firstUnanswered() {
  const k = items.findIndex(i => !i.label);
  return k === -1 ? 0 : k;
}

function renderInstructions() {
  const practice = RUBRIC.practice.map((p, i) => el("div", {class: "card"},
    el("div", {class: "muted"}, "Worked example " + (i + 1)),
    el("div", {class: "rule"}, p.constraint),
    el("div", {class: "resp"}, p.response),
    el("p", {}, el("b", {}, p.answer + ". "), p.note)));
  app.replaceChildren(
    el("h1", {}, "Instructions"),
    el("div", {class: "card"},
       el("div", {style: "white-space: pre-wrap"}, RUBRIC.instructions)),
    el("h2", {}, "Twelve worked examples"), ...practice,
    el("button", {class: "primary", onclick: start},
       "Begin annotating (Enter)"));
}

function start() { view = "annotate"; idx = firstUnanswered(); render(); }

function renderItem() {
  const it = items[idx];
  const answered = items.filter(i => i.label).length;
  app.replaceChildren(
    el("div", {class: "bar"},
       el("span", {}, "Item " + it.display + " of " + items.length),
       el("span", {class: "muted"},
          answered + " / " + items.length + " answered"),
       it.flag ? el("span", {class: "flagged"}, "FLAGGED") : ""),
    el("div", {class: "card"},
       el("div", {class: "muted"}, "Rule"),
       el("div", {class: "rule"}, it.constraint_text)),
    el("div", {class: "card"},
       el("div", {class: "muted"}, "Response"),
       el("div", {class: "resp"}, it.response_text)),
    el("div", {class: "bar"},
       el("button", {class: "primary" + (it.label === "pass" ? " sel" : ""),
                     onclick: () => judge("SATISFIES")},
          "1 · SATISFIES"),
       el("button", {class: "danger" + (it.label === "fail" ? " sel-v" : ""),
                     onclick: () => judge("VIOLATES")},
          "2 · VIOLATES"),
       el("button", {onclick: toggleFlag},
          (it.flag ? "Unflag" : "Flag") + " (F)"),
       el("button", {onclick: () => move(-1)}, "\\u2190 Prev"),
       el("button", {onclick: () => move(1)}, "Next \\u2192"),
       el("button", {onclick: () => { view = "done"; render(); }},
          "Review & submit")),
    el("p", {class: "muted"},
       "Keys: ", el("span", {class: "key"}, "1"), " SATISFIES · ",
       el("span", {class: "key"}, "2"), " VIOLATES · ",
       el("span", {class: "key"}, "F"), " flag · ",
       el("span", {class: "key"}, "\\u2190"), " ",
       el("span", {class: "key"}, "\\u2192"), " navigate. ",
       "Answers save automatically."));
}

let face = null;
function renderDone() {
  const un = items.filter(i => !i.label).map(i => i.display);
  const fl = items.filter(i => i.flag).map(i => i.display);
  const jump = d => el("a", {class: "jump", onclick: () => {
    idx = items.findIndex(i => i.display === d); view = "annotate";
    render(); }}, String(d));
  const canSubmit = un.length === 0 && face !== null && !progress.finalized;
  app.replaceChildren(
    el("h1", {}, "Review & submit"),
    progress.finalized ? el("div", {class: "banner"},
      "Finalised — your labels are immutable.") : "",
    el("div", {class: "card"},
       el("h2", {}, "Unanswered (" + un.length + ")"),
       un.length ? el("div", {}, ...un.map(jump))
                 : el("p", {class: "muted"}, "Every item has an answer.")),
    el("div", {class: "card"},
       el("h2", {}, "Flagged for review (" + fl.length + ")"),
       fl.length ? el("div", {}, ...fl.map(jump))
                 : el("p", {class: "muted"}, "No flags.")),
    el("div", {class: "card"},
       el("h2", {}, "One final judgment"),
       el("p", {}, RUBRIC.face_statement),
       el("p", {class: "rule"}, "Constraint text: ",
          RUBRIC.face_template),
       el("p", {}, RUBRIC.face_question),
       el("div", {class: "bar"},
          el("button", {class: face === true ? "sel" : "",
                        onclick: () => { face = true; render(); }}, "Yes"),
          el("button", {class: face === false ? "sel-v" : "",
                        onclick: () => { face = false; render(); }}, "No"))),
    el("div", {class: "bar"},
       el("button", {onclick: () => { view = "annotate"; render(); }},
          "Back to items"),
       el("button", {class: "primary", disabled: canSubmit ? undefined : "",
                     onclick: submit},
          "Submit — final and immutable")));
}

async function judge(j) {
  if (progress.finalized) return;
  const it = items[idx];
  await api("/api/label", {display: it.display, judgment: j});
  it.label = j === "SATISFIES" ? "pass" : "fail";
  if (idx < items.length - 1) idx += 1; else { view = "done"; }
  render();
}

async function toggleFlag() {
  if (progress.finalized) return;
  const it = items[idx];
  await api("/api/flag", {display: it.display, flag: !it.flag});
  it.flag = !it.flag; render();
}

function move(d) {
  idx = Math.min(items.length - 1, Math.max(0, idx + d)); render();
}

async function submit() {
  await api("/api/finalize", {face_validity: face});
  await refresh(); view = "done"; render();
}

function render() {
  if (view === "instructions") renderInstructions();
  else if (view === "annotate") renderItem();
  else renderDone();
}

document.addEventListener("keydown", e => {
  if (view === "instructions") { if (e.key === "Enter") start(); return; }
  if (view !== "annotate") return;
  if (e.key === "1") judge("SATISFIES");
  else if (e.key === "2") judge("VIOLATES");
  else if (e.key === "f" || e.key === "F") toggleFlag();
  else if (e.key === "ArrowLeft") move(-1);
  else if (e.key === "ArrowRight") move(1);
});

refresh().then(() => { if (progress.finalized) view = "done"; render(); });
</script>
"""

_DASHBOARD_HTML = """<!doctype html>
<meta charset="utf-8">
<title>Gate 1 annotation dashboard</title>
<style>%(css)s</style>
<main id="app"><h1>Gate 1 annotation — researcher dashboard</h1>
<div id="models"></div></main>
<script>
async function api(path, body) {
  const opts = body === undefined ? {} :
    {method: "POST", headers: {"Content-Type": "application/json"},
     body: JSON.stringify(body)};
  const res = await fetch(path, opts);
  return {ok: res.ok, data: await res.json()};
}
function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {}))
    if (k === "onclick") node.onclick = v; else node.setAttribute(k, v);
  for (const c of children)
    node.append(typeof c === "string" ? document.createTextNode(c) : c);
  return node;
}
async function load() {
  const {data} = await api("/api/summary");
  const holder = document.getElementById("models");
  holder.replaceChildren();
  for (const m of data.models) {
    const rows = m.sessions.map(s => el("tr", {},
      el("td", {}, s.annotator),
      el("td", {}, s.labelled + " / " + s.total),
      el("td", {}, String(s.flags)),
      el("td", {}, s.finalized ? "finalised" : "in progress")));
    const card = el("div", {class: "card"},
      el("h2", {}, m.model + " — " + m.items + " items " +
         (m.locked ? "· LOCKED" : "")),
      el("table", {},
         el("tr", {}, el("th", {}, "annotator"), el("th", {}, "progress"),
            el("th", {}, "flags"), el("th", {}, "status")),
         ...rows),
      el("div", {class: "bar"},
         el("button", {onclick: () => diag(m.model, card)},
            "Diagnostics"),
         el("button", {class: "primary",
                       onclick: () => doExport(m.model, card)},
            "Export annotations")),
      el("div", {class: "detail"}));
    holder.append(card);
  }
}
async function diag(model, card) {
  const {ok, data} = await api("/api/diagnostics?model=" + model);
  card.querySelector(".detail").textContent =
    ok ? JSON.stringify(data, null, 2) : (data.error || "hidden");
  card.querySelector(".detail").style.whiteSpace = "pre-wrap";
}
async function doExport(model, card) {
  const {ok, data} = await api("/api/export", {model});
  card.querySelector(".detail").textContent =
    ok ? "Exported: " + data.path : (data.error || "export refused");
}
load();
</script>
"""


class _Handler(BaseHTTPRequestHandler):
    server: "AnnotationServer"

    def log_message(self, *args):                     # quiet
        pass

    def _send(self, code: int, payload: Any, *, html: bool = False) -> None:
        body = (payload if html
                else json.dumps(payload, ensure_ascii=False)).encode()
        self.send_response(code)
        self.send_header("Content-Type",
                         "text/html; charset=utf-8" if html
                         else "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        try:
            self._route("GET")
        except AnnotationWorkflowError as error:
            self._send(409, {"error": str(error)})

    def do_POST(self):
        try:
            self._route("POST")
        except AnnotationWorkflowError as error:
            self._send(409, {"error": str(error)})

    def _route(self, method: str) -> None:
        url = urlparse(self.path)
        srv = self.server
        session = srv.session
        if session is not None:                       # annotator mode
            if method == "GET" and url.path == "/":
                page = _ANNOTATOR_HTML % {
                    "css": _BASE_CSS,
                    "rubric": json.dumps({
                        "instructions": rubric.INSTRUCTIONS,
                        "practice": list(rubric.PRACTICE_EXAMPLES),
                        "face_statement": rubric.FACE_VALIDITY_STATEMENT,
                        "face_template":
                            rubric.FACE_VALIDITY_CONSTRAINT_TEMPLATE,
                        "face_question": rubric.FACE_VALIDITY_QUESTION,
                    })}
                return self._send(200, page, html=True)
            if method == "GET" and url.path == "/api/items":
                return self._send(200, {"items": session.payload(),
                                        "progress": session.progress(),
                                        "interface": INTERFACE_VERSION})
            if method == "POST" and url.path == "/api/label":
                body = self._json_body()
                judgment = body.get("judgment")
                if judgment not in JUDGMENTS:
                    raise AnnotationWorkflowError(
                        "judgment must be SATISFIES or VIOLATES")
                return self._send(200, session.record(
                    int(body["display"]), label=JUDGMENTS[judgment]))
            if method == "POST" and url.path == "/api/flag":
                body = self._json_body()
                return self._send(200, session.record(
                    int(body["display"]), flag=bool(body["flag"])))
            if method == "POST" and url.path == "/api/finalize":
                body = self._json_body()
                if not isinstance(body.get("face_validity"), bool):
                    raise AnnotationWorkflowError(
                        "answer the face-validity question first")
                return self._send(200, session.finalize(
                    face_validity=body["face_validity"]))
        else:                                          # researcher mode
            if method == "GET" and url.path == "/":
                return self._send(200, _DASHBOARD_HTML % {"css": _BASE_CSS},
                                  html=True)
            if method == "GET" and url.path == "/api/summary":
                return self._send(200, {"models": [
                    summary(srv.workspace, model, packet)
                    for model, packet in sorted(srv.packets.items())]})
            if method == "GET" and url.path == "/api/diagnostics":
                model = parse_qs(url.query).get("model", [""])[0]
                packet = srv.packets.get(model)
                if packet is None:
                    raise AnnotationWorkflowError(f"unknown model {model!r}")
                return self._send(200, diagnostics(
                    srv.workspace, model, packet))
            if method == "POST" and url.path == "/api/export":
                model = self._json_body().get("model", "")
                packet = srv.packets.get(model)
                if packet is None:
                    raise AnnotationWorkflowError(f"unknown model {model!r}")
                path = export_annotations(srv.workspace, model, packet)
                return self._send(200, {"path": str(path)})
        self._send(404, {"error": "not found"})


class AnnotationServer(HTTPServer):
    """Single-threaded on purpose: requests (and autosaves) serialise."""

    def __init__(self, port: int, *, session: AnnotatorSession | None,
                 workspace: Path | None = None,
                 packets: dict[str, Path] | None = None):
        super().__init__(("127.0.0.1", port), _Handler)
        self.session = session
        self.workspace = Path(workspace) if workspace else None
        self.packets = packets or {}


def default_workspace() -> Path:
    from dci1v3.engine.context import DCI1_ROOT
    return DCI1_ROOT / "annotations"


def discover_packets() -> dict[str, Path]:
    from dci1v3.engine.context import registered_context
    from dci1v3.engine.paths import model_tree
    from dci1v3.models.registry import MODEL_KEYS
    packets = {}
    for model in MODEL_KEYS:
        path = model_tree(registered_context(), model).data_dir("gate1") \
            / "annotation_packet.jsonl"
        if path.exists():
            packets[model] = path
    return packets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dci1v3.annotation.server")
    parser.add_argument("--model")
    parser.add_argument("--annotator")
    parser.add_argument("--dashboard", action="store_true")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--packet", default=None,
                        help="explicit packet path (defaults to the "
                             "registered evidence tree)")
    args = parser.parse_args(argv)
    workspace = Path(args.workspace) if args.workspace \
        else default_workspace()
    if args.dashboard:
        server = AnnotationServer(args.port or 8766, session=None,
                                  workspace=workspace,
                                  packets=discover_packets())
        role = "dashboard"
    else:
        if not (args.model and args.annotator):
            parser.error("--model and --annotator are required (or use "
                         "--dashboard)")
        packet = Path(args.packet) if args.packet else \
            discover_packets().get(args.model)
        if packet is None:
            parser.error(f"no annotation packet found for {args.model}")
        session = AnnotatorSession(packet_path=packet, workspace=workspace,
                                   model=args.model,
                                   annotator=args.annotator)
        server = AnnotationServer(args.port or 8765, session=session)
        role = f"annotator {args.annotator} on {args.model}"
    print(f"Serving {role} at http://127.0.0.1:{server.server_port}/ "
          f"(Ctrl+C stops; work is saved on every keypress)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
