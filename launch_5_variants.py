#!/usr/bin/env python3
"""
SW-1 Alpha — 5-Instance Parallel Launcher
----------------------------------------
Launches 5 JarvisLabs instances for variants A/C/D/H/J.

Usage:
    python launch_5_variants.py
    python launch_5_variants.py --dry-run
    python launch_5_variants.py --variants A D J
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime


def _jl_slug(s: str, max_len: int = 32) -> str:
    t = "".join(c if c.isalnum() or c in "-_" else "-" for c in s.lower())
    while "--" in t:
        t = t.replace("--", "-")
    t = t.strip("-")[:max_len]
    return t or "x"


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

API_KEY = (os.environ.get("JL_API_KEY") or "").strip()
if not API_KEY:
    API_KEY = "mgMHYQlRZqsDXo988uk1Ux4uzRxTeXAxScvRNU3QTgA"
os.environ["JL_API_KEY"] = API_KEY

INSTANCE_OWNER = _jl_slug(os.environ.get("INSTANCE_OWNER", "cursor"), 20)
GPU_TYPE = "H100"
STORAGE_GB = 300
PIPELINE_SCRIPT = "wan_pipeline_5_variants.py"
REQUIREMENTS_FILE = "requirements_v2.txt"

_ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL_PIPELINE_PATH = os.path.join(_ROOT, PIPELINE_SCRIPT)
LOCAL_REQUIREMENTS_PATH = os.path.join(_ROOT, REQUIREMENTS_FILE)

STATUS_FILE = os.path.join(_ROOT, "variant_status_5.json")
LOG_DIR = os.path.join(_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

VARIANTS = {
    "A": "Standard Night",
    "C": "Golden Hour Dawn",
    "D": "Neon Cyberpunk",
    "H": "IMAX Documentary",
    "J": "Anime Stylized",
}


def log(msg, variant=None):
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = f"[{ts}]"
    if variant:
        prefix += f" [{variant}:{VARIANTS.get(variant, '')}]"
    print(f"{prefix} {msg}")


def update_status(variant, status, details=""):
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
    except Exception:
        data = {}

    data[variant] = {
        "style": VARIANTS.get(variant, "Unknown"),
        "status": status,
        "details": details,
        "updated": datetime.now().isoformat(),
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def build_instance_name(variant_key: str) -> str:
    style_slug = _jl_slug(VARIANTS[variant_key].lower().replace(" ", "-"), 28)
    raw = f"{INSTANCE_OWNER}-sw1-5v-{variant_key.lower()}-{style_slug}"
    return raw[:63].rstrip("-")


def format_remote_launcher(instance_name: str, variant_key: str, use_fast: bool) -> str:
    fast_tail = ", '--fast'" if use_fast else ""
    return f"""
import os, sys
os.environ['JL_API_KEY'] = {repr(API_KEY)}
from jarvislabs.cli.app import main
sys.argv = ['jl', 'run', {repr(LOCAL_PIPELINE_PATH)},
    '--gpu', {repr(GPU_TYPE)},
    '--storage', {repr(str(STORAGE_GB))},
    '--name', {repr(instance_name)},
    '--requirements', {repr(LOCAL_REQUIREMENTS_PATH)},
    '--keep', '--yes',
    '--', '--variant', {repr(variant_key)}{fast_tail}]
main()
"""


def launch_variant(variant_key, dry_run=False, use_fast=True):
    instance_name = build_instance_name(variant_key)
    log(f"Launching instance: {instance_name}", variant_key)
    update_status(variant_key, "LAUNCHING", instance_name)

    if dry_run:
        log(f"[DRY RUN] would launch {variant_key}", variant_key)
        update_status(variant_key, "DRY_RUN")
        return None

    launcher_code = format_remote_launcher(instance_name, variant_key, use_fast)
    log_file = os.path.join(LOG_DIR, f"variant_5_{variant_key}.log")
    with open(log_file, "w", encoding="utf-8") as lf:
        proc = subprocess.Popen(
            [sys.executable, "-c", launcher_code],
            stdout=lf,
            stderr=subprocess.STDOUT,
            cwd=_ROOT,
        )
    update_status(variant_key, "RUNNING", f"PID={proc.pid} | {instance_name}")
    log(f"PID {proc.pid} -> {log_file}", variant_key)
    return proc


def main():
    parser = argparse.ArgumentParser(description="Launch 5 SW-1 variants")
    parser.add_argument(
        "--variants",
        nargs="+",
        default=list(VARIANTS.keys()),
        choices=list(VARIANTS.keys()),
        help="Variant list (default: all 5)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="Seconds between launches (default: 5)",
    )
    parser.add_argument(
        "--gpu",
        type=str,
        default="H100",
        help="GPU type (default: H100)",
    )
    parser.add_argument(
        "--no-fast",
        action="store_true",
        help="Disable fast mode",
    )
    args = parser.parse_args()

    global GPU_TYPE
    GPU_TYPE = args.gpu
    use_fast = not args.no_fast

    print("=" * 65)
    print("  SW-1 ALPHA — 5 VARIANT PARALLEL LAUNCH")
    print("=" * 65)
    print(f"GPU: {GPU_TYPE} | Storage: {STORAGE_GB}GB")
    print(f"Variants: {', '.join(args.variants)}")
    print(f"Fast mode: {use_fast}")
    print(f"Status file: {STATUS_FILE}")
    print("=" * 65)

    processes = []
    for i, variant in enumerate(args.variants):
        p = launch_variant(variant, dry_run=args.dry_run, use_fast=use_fast)
        if p:
            processes.append((variant, p))
        if i < len(args.variants) - 1 and not args.dry_run:
            time.sleep(args.delay)

    if args.dry_run:
        print("Dry run complete.")
        return

    print("\nLaunched:")
    for variant, proc in processes:
        print(f"- {variant} ({VARIANTS[variant]}): PID {proc.pid}")
    print("\nMonitor with logs in logs/ and status in variant_status_5.json")


if __name__ == "__main__":
    main()
