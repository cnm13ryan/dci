"""dci — the reproducible command-line workflow.

  dci doctor [--gpu]          environment report; exit 30 when unsupported
  dci test                    CPU test suite (pytest -m "not gpu and not slow")
  dci plan     --profile P    inspect config and designs; generates NOTHING
  dci qualify  --profile P    pre-confirmatory gates and throughput benchmark,
                              which do generate; needs --execute for evidence
  dci run      --profile P    execute the pipeline for the profile
  dci validate --profile integration_pass
                              run and ASSERT the frozen no-bypass baseline
  dci report   <run_root>     print STATUS/gates of a finished run

Evidence-producing safeguard: profiles whose model profile produces evidence
(`study`, and `pilot` for real generation) refuse to run without --execute, and
always refuse while the environment doctor fails. `plan` needs no such guard
because it cannot generate: it stops before the first generating stage AND runs
with planning_only, so the inference seam refuses to hand it a usable backend.
Stages that must generate before confirmation live behind `dci qualify`.
Scientific stops exit 10 and are not crashes; see dci/pipeline/runner.py for
the taxonomy.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from dci.config import loader


def _activate(args) -> None:
    if getattr(args, "profile", None):
        path = Path(args.profile)
        if not path.exists():
            path = Path("configs/profiles") / f"{args.profile}.toml"
        cfg = loader.load_profile(path)
    else:
        cfg = loader.ActiveConfig()
    if getattr(args, "data_root", None):
        cfg.data_root = args.data_root
    if getattr(args, "device", None) is not None:
        cfg.device_index = args.device
    if getattr(args, "shard", None):
        idx, total = args.shard.split("/")
        cfg.shard_index, cfg.shard_total = int(idx), int(total)
    if getattr(args, "run_id", None):
        cfg.run_id = args.run_id
    loader.activate(cfg)


def _guard_evidence(args) -> None:
    from dci.config.loader import ACTIVE
    evidence_capable = (ACTIVE.model_profile in ("pilot", "study")
                        and not ACTIVE.dry_run_mode)
    if evidence_capable and not args.execute:
        print(f"profile {ACTIVE.model_profile!r} with dry_run_mode=false can "
              "spend real GPU time"
              + (" and produce SCIENTIFIC evidence" if ACTIVE.model_profile == "study" else "")
              + ".\nRe-run with --execute after reviewing `dci plan`.")
        sys.exit(2)


def cmd_run(args) -> int:
    _activate(args)
    _guard_evidence(args)
    from dci.pipeline.runner import run_pipeline
    return run_pipeline(until=getattr(args, "until", None))


# The last stage that generates nothing. c222 (Gate 0) runs a micro-generation
# self-test and c242 runs the throughput benchmark, so a planning command that
# reached either of those would generate for real under a non-dry-run profile.
PLAN_LAST_STAGE = "c216"

# The pre-confirmatory qualification boundary: Gate 0, Gate M and the throughput
# benchmark. These DO generate, which v19 requires of them, so the command that
# runs them is explicit and guarded rather than advertised as planning.
QUALIFY_LAST_STAGE = "c242"


def cmd_plan(args) -> int:
    """Inspect the frozen configuration and the design. Generates nothing.

    Two independent guarantees, because one is an arrangement and the other is
    structural: the traversal stops before the first stage that can generate,
    AND planning_only makes the inference seam hand out a backend that refuses.
    """
    _activate(args)
    from dci.config import loader
    loader.ACTIVE.planning_only = True
    from dci.pipeline.runner import run_pipeline
    code = run_pipeline(until=PLAN_LAST_STAGE)
    print(f"\n[plan] stopped after {PLAN_LAST_STAGE} with no generation "
          "attempted. The measured throughput and budget projection need the "
          "benchmark, which generates: run `dci qualify` for those.")
    return code


def cmd_qualify(args) -> int:
    """Run the pre-confirmatory qualification stages, which DO generate.

    Gate 0's micro-generation, Gate M's measurement audit and the throughput
    benchmark are executable pre-confirmatory work, not planning. The evidence
    guard therefore applies exactly as it does to `run`.
    """
    _activate(args)
    _guard_evidence(args)
    from dci.pipeline.runner import run_pipeline
    code = run_pipeline(until=QUALIFY_LAST_STAGE)
    print(f"\n[qualify] stopped after {QUALIFY_LAST_STAGE}; review the gate "
          "trace, projection and budget snapshots above before `dci run`.")
    return code


def cmd_validate(args) -> int:
    args.profile = args.profile or "integration_pass"
    _activate(args)
    from dci.pipeline.runner import EXIT_SCIENTIFIC, run_pipeline
    from dci.pipeline import state as S
    code = run_pipeline()
    trace = [(g, o.status, o.dry_run_bypassed)
             for g, o in getattr(S, "GATE_STATE", {}).items()]
    print("\n[validate] gate trace:")
    for g, status, byp in trace:
        print(f"  {g:20s} {status}" + ("   [BYPASS]" if byp else ""))
    expected = [("0_implementation", "PASS"), ("M_measurement", "PASS"),
                ("1_u_bank", "PASS"), ("2a_precision", "PASS"),
                ("2_feasibility", "NOT_IDENTIFIED_SUPPORT")]
    got = [(g, s) for g, s, _ in trace]
    ok = (code == EXIT_SCIENTIFIC and not any(b for *_, b in trace)
          and all(e in got for e in expected))
    print(f"\n[validate] baseline {'REPRODUCED' if ok else 'NOT reproduced'} "
          f"(exit {code}; expected scientific stop with zero bypasses).")
    return 0 if ok else 1


def cmd_report(args) -> int:
    root = Path(args.run_root)
    status = root / "exports"
    for p in sorted(root.glob("exports/*/STATUS.txt")):
        print(f"--- {p}\n{p.read_text()}")
    gates = sorted(root.glob("gates/gate_*.json"))
    for g in gates:
        d = json.loads(g.read_text())
        print(f"{d.get('gate','?'):22s} {d.get('status')}"
              + ("  [BYPASS]" if d.get("dry_run_bypassed") else ""))
    stop = root / "stop.json"
    if stop.exists():
        print("\nstop.json:", stop.read_text())
    return 0


def cmd_test(args) -> int:
    marks = "not gpu and not slow and not cloud"
    return subprocess.call([sys.executable, "-m", "pytest", "-q", "-m", marks])


def cmd_doctor(args) -> int:
    """In-process, from the installed package.

    This used to shell out to scripts/local_doctor.py, which is not part of the
    distribution: on any checkout that has the package but not the repository
    working tree - a wheel install, or any snapshot of this stack before the
    scripts land - the advertised command failed with a Python file-not-found.
    """
    from dci import diagnostics
    return diagnostics.run(gpu=args.gpu,
                           expect_devices=getattr(args, "expect_devices", None))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="dci", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--profile", default=None)
        p.add_argument("--data-root", default=None)
        p.add_argument("--device", type=int, default=None)
        p.add_argument("--shard", default=None, help="i/N deterministic worker shard")
        p.add_argument("--run-id", default=None)
        p.add_argument("--execute", action="store_true",
                       help="required for evidence-capable profiles")

    p = sub.add_parser("run", help="execute the pipeline"); common(p)
    p.add_argument("--until", default=None, help="stop after stage prefix, e.g. c222")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("plan", help="config + designs only; generates nothing")
    common(p); p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("qualify",
                       help="pre-confirmatory gates and throughput benchmark; "
                            "GENERATES")
    common(p); p.set_defaults(fn=cmd_qualify)
    p = sub.add_parser("validate", help="assert the frozen no-bypass baseline")
    common(p); p.set_defaults(fn=cmd_validate)
    p = sub.add_parser("report"); p.add_argument("run_root"); p.set_defaults(fn=cmd_report)
    p = sub.add_parser("test"); p.set_defaults(fn=cmd_test)
    p = sub.add_parser("doctor"); p.add_argument("--gpu", action="store_true")
    p.add_argument("--expect-devices", type=int, default=None,
                   help="fail unless exactly this many GPUs are visible")
    p.set_defaults(fn=cmd_doctor)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
