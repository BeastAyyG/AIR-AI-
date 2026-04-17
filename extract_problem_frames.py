#!/usr/bin/env python3
"""
Extract specific frames from FINAL_WAN22_MOVIE.mp4 for visual inspection.
This tells us EXACTLY where the wrong text is so we can fix it precisely.
"""
import subprocess, os, sys

INPUT = r"C:\happy horse\ALL_VIDEOS\FINAL_WAN22_MOVIE.mp4"
OUT_DIR = r"C:\happy horse\ALL_VIDEOS\PROBLEM_FRAMES"
os.makedirs(OUT_DIR, exist_ok=True)

ffmpeg = "ffmpeg"

# Each problem: (timestamp_seconds, label)
FRAMES = [
    (20.5, "0m20s_CRITICAL_TRAMUA_HIGHWAY"),
    (21.0, "0m21s_monitor_gibberish"),
    (25.5, "0m25s_SLLAO_drone_chassis"),
    (27.0, "0m27s_drone_morphing_tiltrotor"),
    (36.0, "0m35s_white_drone_takeoff"),
    (42.0, "0m41s_white_quadcopter_traffic"),
    (46.0, "0m46s_GOOD_REFERENCE_drone"),   # the correct SW-1 at 0:46
    (52.0, "0m51s_radar_fixedwing_vitals"),
    (53.0, "0m53s_vitals_kisszach_text"),
    (57.0, "0m56s_white_jet_helipad"),
    (62.0, "1m01s_blue_quadcopter_landing"),
    (77.0, "1m16s_W_BAP_LITA_MINUTES"),
    (82.0, "1m21s_SW1_ALPFGE_endtitle"),
]

print(f"Extracting {len(FRAMES)} reference frames from:\n  {INPUT}\n")

for ts, label in FRAMES:
    out = os.path.join(OUT_DIR, f"{label}.png")
    cmd = [
        ffmpeg, "-y",
        "-ss", str(ts),
        "-i", INPUT,
        "-frames:v", "1",
        "-q:v", "2",
        out
    ]
    r = subprocess.run(cmd, capture_output=True)
    size = os.path.getsize(out) if os.path.exists(out) else 0
    status = f"OK ({size//1024} KB)" if size > 0 else "FAILED"
    print(f"  {status:12s}  {ts:5.1f}s  {label}.png")

print(f"\nDone! Open these frames to identify exact text positions:")
print(f"  {OUT_DIR}")
