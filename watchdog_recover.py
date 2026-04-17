#!/usr/bin/env python3
import json
import os
import re
import subprocess
import time
from datetime import datetime


API_KEY = (
    os.environ.get("JL_API_KEY", "").strip()
    or "mgMHYQlRZqsDXo988uk1Ux4uzRxTeXAxScvRNU3QTgA"
)
os.environ["JL_API_KEY"] = API_KEY

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(ROOT, "logs")

VARIANT_MACHINE = {
    "A": 396762,
    "B": 396763,
    "C": 396764,
    "D": 396765,
    "E": 396766,
    "F": 396768,
    "G": 396767,
    "H": 396770,
    "I": 396769,
    # Keep J on the dedicated max setup if available
    "J": 396830,
}


def now():
    return datetime.now().strftime("%H:%M:%S")


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return p.returncode, p.stdout, p.stderr


def latest_run_id(variant):
    path = os.path.join(LOG_DIR, f"variant_{variant}.log")
    if not os.path.exists(path):
        return None
    txt = open(path, "r", encoding="utf-8", errors="ignore").read()
    ids = re.findall(r"Run ID:\s*(r_[a-z0-9]+)", txt)
    return ids[-1] if ids else None


def append_run_id(variant, rid):
    path = os.path.join(LOG_DIR, f"variant_{variant}.log")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n[watchdog {now()}] Restarted run\nRun ID: {rid}\n")


def state_for_run(run_id):
    rc, out, err = run(["jl", "run", "status", run_id])
    if rc != 0:
        return "unknown", out + err
    m = re.search(r"State:\s*([^\n\r]+)", out)
    return (m.group(1).strip().lower() if m else "unknown"), out


def start_variant_on_machine(variant, machine_id):
    cmd = [
        "jl",
        "run",
        "wan_pipeline_v2.py",
        "--on",
        str(machine_id),
        "--requirements",
        "requirements_v2.txt",
        "--yes",
        "--",
        "--variant",
        variant,
        "--fast",
    ]
    rc, out, err = run(cmd)
    txt = out + "\n" + err
    m = re.search(r"Run ID:\s*(r_[a-z0-9]+)", txt)
    return rc == 0 and m is not None, (m.group(1) if m else None), txt


def active_instances():
    rc, out, err = run(["jl", "list", "--json"])
    if rc != 0:
        return []
    try:
        return json.loads(out)
    except Exception:
        return []


def monitor_once():
    print(f"[{now()}] Watchdog tick")
    active = {int(x["machine_id"]) for x in active_instances() if "machine_id" in x}
    for variant in "ABCDEFGHIJ":
        rid = latest_run_id(variant)
        mid = VARIANT_MACHINE.get(variant)
        if rid:
            state, _ = state_for_run(rid)
            if state in {"running", "queued", "starting"}:
                print(f"  {variant}: ok ({state})")
                continue
            if state in {"completed", "success"}:
                print(f"  {variant}: completed")
                continue
            print(f"  {variant}: not active ({state}), attempting restart...")
        else:
            print(f"  {variant}: no run id, attempting start...")

        if mid and mid in active:
            ok, new_rid, msg = start_variant_on_machine(variant, mid)
            if ok and new_rid:
                append_run_id(variant, new_rid)
                print(f"  {variant}: restarted as {new_rid}")
            else:
                print(f"  {variant}: restart failed")
                print(msg[:300])
        else:
            print(f"  {variant}: machine {mid} not active, skip")


def main():
    while True:
        monitor_once()
        time.sleep(120)


if __name__ == "__main__":
    main()
