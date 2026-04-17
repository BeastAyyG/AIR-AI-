#!/usr/bin/env python3
"""
SW-1 Alpha — 10-Instance Parallel Launcher
============================================
Spins up 10 H100 instances on JarvisLabs simultaneously,
each generating a different cinematic style variant.

Usage:
    python launch_10_variants.py              # Launch all 10
    python launch_10_variants.py --variants A B C  # Launch specific variants
    python launch_10_variants.py --dry-run    # Preview without launching
"""

import sys
import os
import subprocess
import time
import argparse
import json
from datetime import datetime

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ============================================================================
# CONFIG
# ============================================================================


def _jl_slug(s: str, max_len: int = 32) -> str:
    t = "".join(c if c.isalnum() or c in "-_" else "-" for c in s.lower())
    while "--" in t:
        t = t.replace("--", "-")
    t = t.strip("-")[:max_len]
    return t or "x"


INSTANCE_OWNER = _jl_slug(os.environ.get("INSTANCE_OWNER", "cursor"), 20)

API_KEY = (os.environ.get("JL_API_KEY") or "").strip()
if not API_KEY:
    # Fallback so local runs keep working; prefer setting JL_API_KEY in your environment.
    API_KEY = "mgMHYQlRZqsDXo988uk1Ux4uzRxTeXAxScvRNU3QTgA"
os.environ["JL_API_KEY"] = API_KEY


def build_instance_name(variant_key: str) -> str:
    style_slug = _jl_slug(VARIANTS[variant_key].lower().replace(" ", "-"), 28)
    raw = f"{INSTANCE_OWNER}-sw1-{variant_key.lower()}-{style_slug}"
    if len(raw) > 63:
        return raw[:63].rstrip("-")
    return raw


def format_remote_launcher(instance_name: str, variant_key: str, use_fast: bool) -> str:
    fast_tail = ", '--fast'" if use_fast else ""
    return f"""
import sys, os
os.environ["JL_API_KEY"] = {repr(API_KEY)}
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


VARIANTS = {
    "A": "Standard Night",
    "B": "Monsoon Storm",
    "C": "Golden Hour Dawn",
    "D": "Neon Cyberpunk",
    "E": "Handheld Documentary",
    "F": "Arctic Blizzard",
    "G": "Desert Afternoon",
    "H": "IMAX Documentary",
    "I": "Film Noir BW",
    "J": "Anime Stylized",
}

GPU_TYPE = "H100"
STORAGE_GB = 300
PIPELINE_SCRIPT = "wan_pipeline_v2.py"
REQUIREMENTS_FILE = "requirements_v2.txt"
# Single-file jl target uses SCP (works on Windows). Directory target "." requires rsync.
_ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL_PIPELINE_PATH = os.path.join(_ROOT, PIPELINE_SCRIPT)
LOCAL_REQUIREMENTS_PATH = os.path.join(_ROOT, REQUIREMENTS_FILE)

# Status tracking
STATUS_FILE = os.path.join(os.path.dirname(__file__), "variant_status.json")
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)


def log(msg, variant=None):
    """Print timestamped log message."""
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = f"[{ts}]"
    if variant:
        prefix += f" [{variant}:{VARIANTS.get(variant, '')}]"
    print(f"{prefix} {msg}")


def update_status(variant, status, details=""):
    """Update the JSON status tracker."""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as f:
                data = json.load(f)
        else:
            data = {}
    except (json.JSONDecodeError, FileNotFoundError):
        data = {}

    data[variant] = {
        "style": VARIANTS.get(variant, "Unknown"),
        "status": status,
        "details": details,
        "updated": datetime.now().isoformat(),
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def launch_variant(variant_key, dry_run=False, use_fast=True):
    """Launch a single JarvisLabs H100 instance for one variant."""
    instance_name = build_instance_name(variant_key)

    log(f"🚀 Launching instance: {instance_name}", variant_key)
    update_status(variant_key, "LAUNCHING", instance_name)

    if dry_run:
        log(
            f"   [DRY RUN] Would launch: {instance_name} with --variant {variant_key}",
            variant_key,
        )
        update_status(variant_key, "DRY_RUN")
        return

    try:
        from jarvislabs.cli.app import main as jl_main

        # Save original argv
        orig_argv = sys.argv[:]

        argv_tail = ["--variant", variant_key]
        if use_fast:
            argv_tail.append("--fast")
        sys.argv = [
            "jl",
            "run",
            LOCAL_PIPELINE_PATH,
            "--gpu",
            GPU_TYPE,
            "--storage",
            str(STORAGE_GB),
            "--name",
            instance_name,
            "--requirements",
            LOCAL_REQUIREMENTS_PATH,
            "--keep",
            "--yes",
            "--",
            *argv_tail,
        ]

        log(
            f"   Command: jl run {PIPELINE_SCRIPT} --gpu {GPU_TYPE} --name {instance_name} --variant {variant_key}",
            variant_key,
        )
        update_status(variant_key, "RUNNING", instance_name)

        # Run in a separate thread-safe way
        try:
            jl_main()
            update_status(variant_key, "COMPLETE", instance_name)
            log(f"✅ COMPLETE", variant_key)
        except SystemExit:
            # jl CLI sometimes calls sys.exit
            update_status(variant_key, "COMPLETE", instance_name)
            log(f"✅ Instance launched (CLI exited)", variant_key)
        except Exception as e:
            update_status(variant_key, "ERROR", str(e))
            log(f"❌ Error: {e}", variant_key)

        # Restore argv
        sys.argv = orig_argv

    except ImportError:
        # Fallback: use subprocess to call jl directly
        log(f"   Using subprocess fallback...", variant_key)
        fast = ", '--fast'" if use_fast else ""
        cmd = [
            sys.executable,
            "-c",
            f"""
import sys, os
os.environ['JL_API_KEY'] = {repr(API_KEY)}
from jarvislabs.cli.app import main
sys.argv = ['jl', 'run', {repr(LOCAL_PIPELINE_PATH)},
    '--gpu', {repr(GPU_TYPE)},
    '--storage', {repr(str(STORAGE_GB))},
    '--name', {repr(instance_name)},
    '--requirements', {repr(LOCAL_REQUIREMENTS_PATH)},
    '--destroy', '--yes',
    '--', '--variant', {repr(variant_key)}{fast}]
main()
""",
        ]
        log_file = os.path.join(LOG_DIR, f"variant_{variant_key}.log")
        with open(log_file, "w") as lf:
            proc = subprocess.Popen(
                cmd,
                stdout=lf,
                stderr=subprocess.STDOUT,
                cwd=os.path.dirname(__file__),
            )
        update_status(variant_key, "RUNNING_PID_" + str(proc.pid), instance_name)
        log(f"   PID {proc.pid} → Log: {log_file}", variant_key)


def launch_sequential(variant_key, dry_run=False, use_fast=True):
    """Launch variant via subprocess so each gets its own process."""
    instance_name = build_instance_name(variant_key)

    log(f"🚀 Launching instance: {instance_name}", variant_key)
    update_status(variant_key, "LAUNCHING", instance_name)

    if dry_run:
        log(f"   [DRY RUN] Would launch: {instance_name}", variant_key)
        return

    launcher_code = format_remote_launcher(instance_name, variant_key, use_fast)
    log_file = os.path.join(LOG_DIR, f"variant_{variant_key}.log")

    proc = subprocess.Popen(
        [sys.executable, "-c", launcher_code],
        stdout=open(log_file, "w"),
        stderr=subprocess.STDOUT,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )

    update_status(variant_key, "RUNNING", f"PID={proc.pid} | {instance_name}")
    log(f"   Started PID {proc.pid} → {log_file}", variant_key)
    return proc


def main():
    parser = argparse.ArgumentParser(
        description="Launch 10 parallel SW-1 Alpha generation instances"
    )
    parser.add_argument(
        "--variants",
        nargs="+",
        default=list(VARIANTS.keys()),
        choices=list(VARIANTS.keys()),
        help="Which variants to launch (default: all 10)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview commands without actually launching",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="Seconds between launches to avoid API rate limits (default: 5)",
    )
    parser.add_argument(
        "--gpu",
        type=str,
        default="H100",
        help="GPU type to request (default: H100, fallback: A100)",
    )
    parser.add_argument(
        "--no-fast",
        action="store_true",
        help="Do not pass --fast to remote wan_pipeline_v2.py (slower, higher quality)",
    )
    args = parser.parse_args()

    # Override global GPU config
    global GPU_TYPE
    GPU_TYPE = args.gpu

    print()
    print("=" * 65)
    print("  SW-1 ALPHA — MULTI-INSTANCE GENERATION")
    print("=" * 65)
    use_fast_remote = not args.no_fast
    print(f"  GPU: {GPU_TYPE} | Storage: {STORAGE_GB}GB each")
    print(f"  Instance owner: {INSTANCE_OWNER} | Remote --fast: {use_fast_remote}")
    print(f"  Variants: {', '.join(args.variants)} ({len(args.variants)} instances)")
    print(f"  Delay between launches: {args.delay}s")
    print(f"  Status file: {STATUS_FILE}")
    print(f"  Log directory: {LOG_DIR}")
    print("=" * 65)
    print()

    # Show variant table
    print("  VARIANT    STYLE                   STATUS")
    print("  " + "-" * 50)
    for v in args.variants:
        marker = "🟢 QUEUED" if not args.dry_run else "⚪ DRY RUN"
        print(f"  {v}          {VARIANTS[v]:<24s}{marker}")
    print()

    if not args.dry_run:
        print(
            f"⚠️  This will launch {len(args.variants)} H100 instances simultaneously!"
        )
        print(
            f"   Estimated cost: ~${len(args.variants) * 3:.0f}-${len(args.variants) * 5:.0f}/hr"
        )
        print(
            "   Estimated time: highly variable (parallel H100s; 80s final + loop export)"
        )
        print()

    # Launch all variants
    processes = []
    for i, variant_key in enumerate(args.variants):
        log(f"--- Launching variant {i + 1}/{len(args.variants)} ---")
        proc = launch_sequential(variant_key, args.dry_run, use_fast_remote)
        if proc:
            processes.append((variant_key, proc))

        if i < len(args.variants) - 1 and not args.dry_run:
            log(f"   Waiting {args.delay}s before next launch...")
            time.sleep(args.delay)

    if args.dry_run:
        print("\n✅ Dry run complete. No instances were launched.")
        return

    # Summary
    print()
    print("=" * 65)
    print(f"  🎬 ALL {len(processes)} INSTANCES LAUNCHED!")
    print("=" * 65)
    print(f"  Monitor status:  python check_variants.py")
    print(f"  Status file:     {STATUS_FILE}")
    print(f"  Logs directory:  {LOG_DIR}")
    print()

    for v, p in processes:
        print(f"  Variant {v} ({VARIANTS[v]}): PID {p.pid}")

    print()
    print("  Each instance will auto-destroy after generation completes.")
    print("  Use 'python check_variants.py' to monitor progress.")
    print("=" * 65)


if __name__ == "__main__":
    main()
