#!/usr/bin/env python3
"""
SW-1 Alpha — Seamless Segment Rejoiner
======================================
Stitches the GOOD segments and REFINED segments back
together in the original order using ffmpeg concatenate.

Run this AFTER refinement is complete and files are downloaded.
"""

import os
import json
import subprocess
import sys

# ─── CONFIG ────────────────────────────────────────────────────────────────────
PLAN_FILE = r"C:\happy horse\ALL_VIDEOS\segment_plan.json"
OUTPUT_MOVIE = r"C:\happy horse\ALL_VIDEOS\REJOINED_FINAL_MOVIE.mp4"
LIST_FILE = r"C:\happy horse\ALL_VIDEOS\concat_list.txt"


def find_ffmpeg():
    candidates = [
        "ffmpeg",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
    ]
    for c in candidates:
        try:
            if subprocess.run([c, "-version"], capture_output=True).returncode == 0:
                return c
        except:
            continue
    return None


def main():
    if not os.path.exists(PLAN_FILE):
        print("ERROR: Segment plan not found.")
        return

    ffmpeg_bin = find_ffmpeg()
    if not ffmpeg_bin:
        print("ERROR: ffmpeg not found.")
        return

    with open(PLAN_FILE, "r") as f:
        plan = json.load(f)

    print("=" * 60)
    print("  SW-1 Alpha — Seamless Video Rejoiner")
    print("=" * 60)

    # Build the ffmpeg concat list
    # We prefer the _REFINED version for BAD segments if it exists
    with open(LIST_FILE, "w", encoding="utf-8") as f:
        for seg in plan:
            path = seg["path"]
            if seg["type"] == "BAD":
                refined_path = path.replace(".mp4", "_REFINED.mp4")
                if os.path.exists(refined_path):
                    path = refined_path
                    print(f"  [+] Using FIXED segment:   {seg['label']}")
                else:
                    print(
                        f"  [!] WARNING: Fixed version of {seg['label']} NOT FOUND. Using original."
                    )
            else:
                print(f"  [ ] Using original segment: {seg['label']}")

            # Escape path for ffmpeg concat file
            escaped_path = path.replace("\\", "/")
            f.write(f"file '{escaped_path}'\n")

    print("\nJoining segments into final movie...")

    # Run ffmpeg concat
    cmd = [
        ffmpeg_bin,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        LIST_FILE,
        "-c",
        "copy",  # Lossless join
        OUTPUT_MOVIE,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"\nSUCCESS! Final movie saved to:\n   {OUTPUT_MOVIE}")
    else:
        print(f"\nERROR rejoining video:\n{result.stderr[-800:]}")


if __name__ == "__main__":
    main()
