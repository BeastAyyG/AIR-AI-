#!/usr/bin/env python3
"""
SW-1 Alpha — Variant Status Checker
=====================================
Monitor the progress of all 10 parallel variant instances.

Usage:
    python check_variants.py         # Check all variants
    python check_variants.py --watch # Live refresh every 30s
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

os.environ["JL_API_KEY"] = "mgMHYQlRZqsDXo988uk1Ux4uzRxTeXAxScvRNU3QTgA"

STATUS_FILE = os.path.join(os.path.dirname(__file__), "variant_status.json")
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")

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


def check_log_tail(variant_key, lines=5):
    """Read last N lines from a variant's log file."""
    log_file = os.path.join(LOG_DIR, f"variant_{variant_key}.log")
    if not os.path.exists(log_file):
        return "[No log file yet]"
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        return "".join(all_lines[-lines:]).strip()
    except Exception as e:
        return f"[Error reading log: {e}]"


def list_instances():
    """List active JarvisLabs instances."""
    try:
        from jarvislabs.cli.app import main as jl_main
        orig_argv = sys.argv[:]
        sys.argv = ["jl", "ls"]
        try:
            jl_main()
        except SystemExit:
            pass
        sys.argv = orig_argv
    except Exception as e:
        print(f"  Could not query JarvisLabs: {e}")


def display_status(show_logs=False):
    """Display the current status of all variants."""
    data = {}
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print()
    print("=" * 70)
    print(f"  SW-1 ALPHA — VARIANT STATUS DASHBOARD  |  {ts}")
    print("=" * 70)
    print()
    print(f"  {'VAR':<4} {'STYLE':<22} {'STATUS':<18} {'UPDATED':<20}")
    print("  " + "-" * 66)

    completed = 0
    running = 0
    errors = 0

    for v in sorted(VARIANTS.keys()):
        style = VARIANTS[v]
        if v in data:
            status = data[v].get("status", "UNKNOWN")
            updated = data[v].get("updated", "")
            if updated:
                try:
                    updated = datetime.fromisoformat(updated).strftime("%H:%M:%S")
                except ValueError:
                    pass
        else:
            status = "NOT STARTED"
            updated = ""

        # Color-code status
        if "COMPLETE" in status:
            icon = "✅"
            completed += 1
        elif "RUNNING" in status:
            icon = "🔄"
            running += 1
        elif "ERROR" in status:
            icon = "❌"
            errors += 1
        elif "LAUNCHING" in status:
            icon = "🚀"
            running += 1
        else:
            icon = "⬜"

        print(f"  {v:<4} {style:<22} {icon} {status:<15} {updated:<20}")

    print()
    print(f"  Summary: {completed} complete | {running} running | {errors} errors | {10 - completed - running - errors} pending")
    print("=" * 70)

    if show_logs:
        print()
        print("  RECENT LOG OUTPUT:")
        print("  " + "-" * 50)
        for v in sorted(VARIANTS.keys()):
            if v in data and "RUNNING" in data[v].get("status", ""):
                tail = check_log_tail(v, 3)
                print(f"\n  [{v}] {VARIANTS[v]}:")
                for line in tail.split("\n"):
                    print(f"    {line}")
        print()

    return completed, running


def main():
    parser = argparse.ArgumentParser(description="Check SW-1 Alpha variant generation status")
    parser.add_argument("--watch", action="store_true", help="Live refresh every 30 seconds")
    parser.add_argument("--logs", action="store_true", help="Show recent log output for running instances")
    parser.add_argument("--instances", action="store_true", help="List active JarvisLabs instances")
    args = parser.parse_args()

    if args.instances:
        print("\n  Active JarvisLabs Instances:")
        print("  " + "-" * 40)
        list_instances()
        return

    if args.watch:
        print("  Live monitoring mode. Press Ctrl+C to stop.\n")
        try:
            while True:
                os.system("cls" if os.name == "nt" else "clear")
                completed, running = display_status(show_logs=args.logs)
                if completed == 10:
                    print("\n  🎉 ALL 10 VARIANTS COMPLETE!")
                    break
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n  Monitoring stopped.")
    else:
        display_status(show_logs=args.logs)


if __name__ == "__main__":
    main()
