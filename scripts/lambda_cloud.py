#!/usr/bin/env python3
"""Lambda Cloud operations for the DCI study. Dry-run by default; every
billable or destructive call requires --execute; nothing here ever substitutes
a GPU SKU (capacity problems are reported, not "solved" with different
hardware, because a different SKU is a different frozen execution class).

Operations mirror the validated runbook (API base https://cloud.lambda.ai/api/v1,
bearer auth, checked against the live docs 2026-07-29 in LAMBDA_CLOUD.md):
doctor, instance-types, launch, wait, instances, terminate. Termination goes
through the API — never `shutdown`/`poweroff` on the instance, which Lambda
documents can leave it billing in Alert status.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request

API = "https://cloud.lambda.ai/api/v1"


def _key() -> str:
    key = os.environ.get("LAMBDA_API_KEY")
    if not key:
        sys.exit("set LAMBDA_API_KEY in this shell (read -rsp ...; export).")
    return key


def call(method: str, path: str, body=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": f"Bearer {_key()}",
                 "Content-Type": "application/json"},
        data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def cmd_instance_types(_):
    data = call("GET", "/instance-types")["data"]
    for name, item in sorted(data.items()):
        t = item["instance_type"]
        regions = [r["name"] for r in item.get(
            "regions_with_capacity_available", [])]
        print(f"{name:22s} {t['price_cents_per_hour']/100:7.2f} $/h  "
              f"regions: {', '.join(regions) or '-'}")
    return 0


def _launch_body(a):
    return {"region_name": a.region, "instance_type_name": a.instance_type,
            "ssh_key_names": [a.ssh_key_name], "file_system_names":
                ([a.filesystem] if a.filesystem else []),
            "quantity": 1, "name": a.name,
            "image": {"family": a.image_family}}


def cmd_doctor(a):
    ok = True
    types = call("GET", "/instance-types")["data"]
    if a.instance_type not in types:
        print(f"[FAIL] instance type {a.instance_type} not offered"); ok = False
    else:
        regions = [r["name"] for r in types[a.instance_type]
                   .get("regions_with_capacity_available", [])]
        hit = a.region in regions
        print(f"[{'ok' if hit else 'FAIL'}] capacity for {a.instance_type} in "
              f"{a.region} (available: {', '.join(regions) or 'none'})")
        ok &= hit
    keys = [k["name"] for k in call("GET", "/ssh-keys")["data"]]
    print(f"[{'ok' if a.ssh_key_name in keys else 'FAIL'}] ssh key "
          f"{a.ssh_key_name!r} in workspace")
    ok &= a.ssh_key_name in keys
    fams = {i.get("family") for i in call("GET", "/images")["data"]}
    print(f"[{'ok' if a.image_family in fams else 'FAIL'}] image family "
          f"{a.image_family!r}")
    ok &= a.image_family in fams
    print("[note] no automatic fallback exists: if capacity is missing, pick a "
          "region from `instance-types` and relaunch explicitly.")
    return 0 if ok else 1


def cmd_launch(a):
    body = _launch_body(a)
    print(json.dumps(body, indent=2))
    if not a.execute:
        print("\nDRY RUN. Re-run with --execute to launch (billable).")
        return 0
    resp = call("POST", "/instance-operations/launch", body)
    print(json.dumps(resp, indent=2))
    if a.state_file:
        os.makedirs(os.path.dirname(a.state_file), exist_ok=True)
        with open(a.state_file, "w") as fh:
            json.dump({"request": body, "response": resp}, fh, indent=2)
    return 0


def cmd_wait(a):
    while True:
        for inst in call("GET", "/instances")["data"]:
            if inst["id"] == a.instance_id:
                print(f"status={inst['status']} ip={inst.get('ip')}",
                      file=sys.stderr)
                if inst["status"] == "active" and inst.get("ip"):
                    print(json.dumps(inst, indent=2))
                    return 0
        time.sleep(15)


def cmd_instances(_):
    data = call("GET", "/instances")["data"]
    if not data:
        print("no instances (nothing is billing).")
    for inst in data:
        print(f"{inst['id']}  {inst['instance_type']['name']:ori<14}"
              if False else
              f"{inst['id']}  {inst['instance_type']['name']:14s} "
              f"{inst['status']:10s} {inst.get('ip')}")
    return 0


def cmd_terminate(a):
    body = {"instance_ids": [a.instance_id]}
    print(json.dumps(body, indent=2))
    if not a.execute:
        print("\nDRY RUN. Re-run with --execute to terminate (destructive: the "
              "root disk is erased; collect and verify artifacts first).")
        return 0
    print(json.dumps(call("POST", "/instance-operations/terminate", body),
                     indent=2))
    print("\nPost-termination inventory:")
    return cmd_instances(a)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def region_args(p):
        p.add_argument("--instance-type", default="gpu_1x_a10")
        p.add_argument("--region", default=os.environ.get("LAMBDA_REGION", ""))
        p.add_argument("--ssh-key-name",
                       default=os.environ.get("LAMBDA_SSH_KEY_NAME", ""))
        p.add_argument("--image-family", default="lambda-stack-24-04")
        p.add_argument("--filesystem", default=None,
                       help="Lambda persistent filesystem to attach at launch")
        p.add_argument("--name", default="dci-v15")
        p.add_argument("--state-file", default=None)
        p.add_argument("--execute", action="store_true")

    p = sub.add_parser("doctor"); region_args(p); p.set_defaults(fn=cmd_doctor)
    p = sub.add_parser("instance-types"); p.set_defaults(fn=cmd_instance_types)
    p = sub.add_parser("launch"); region_args(p); p.set_defaults(fn=cmd_launch)
    p = sub.add_parser("wait"); p.add_argument("--instance-id", required=True)
    p.set_defaults(fn=cmd_wait)
    p = sub.add_parser("instances"); p.set_defaults(fn=cmd_instances)
    p = sub.add_parser("terminate"); p.add_argument("--instance-id", required=True)
    p.add_argument("--execute", action="store_true"); p.set_defaults(fn=cmd_terminate)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
