#!/usr/bin/env python3
"""
SW-1 Alpha — Granular Video Splitter
=====================================
Surgically splits FINAL_WAN22_MOVIE.mp4 into segments based on
the user's EXACT timestamp requests for replacement and correction.

BAD segments (Refine) | GOOD segments (Preserve)
"""

import os
import subprocess
import sys
import json

# ─── CONFIG ────────────────────────────────────────────────────────────────────
INPUT_VIDEO = r"C:\happy horse\ALL_VIDEOS\FINAL_WAN22_MOVIE.mp4"
GOOD_DIR = r"C:\happy horse\ALL_VIDEOS\GOOD_SEGMENTS"
BAD_DIR = r"C:\happy horse\ALL_VIDEOS\BAD_SEGMENTS"
PLAN_FILE = r"C:\happy horse\ALL_VIDEOS\segment_plan.json"

# Shared style and drone design constraints to ensure continuity
DRONE_SPEC = (
    "MUST STRICTLY BE THE SW-1 ALPHA: Autonomous Heavy-Lift Medical Evacuation Octocopter (eVTOL), "
    "flat octocopter with exactly 8 rotors in one horizontal plane around a thick rectangular carbon-fiber core chassis, "
    "rigid cylindrical carbon-fiber tube sub-frame with red chassis nodes and black arm nodes, "
    "8 heavy-lift brushless outrunner motors with large two-blade carbon-fiber propellers, "
    "dark-tinted semi-transparent barrel-vault canopy over a full medical stretcher bed, "
    "fixed 4-point tubular skid landing gear with neon-green brackets, orange/red perimeter LEDs, "
    "internal red/blue emergency strobes, and downward white landing lights. NO quadcopters, NO planes, NO jets."
)
SHARED_STYLE = (
    " Cinematic night lighting, deep navy blue and amber contrast tones, sodium-vapor streetlamp glow, "
    "ultra-realistic, 8k, extreme detail, maintain perfect video continuity with original motion."
)

# Granular segments based on EXACT user request
SEGMENTS = [
    (0.0, 20.0, "seg_01_intro_accident", "GOOD"),
    (
        20.0,
        24.0,
        "seg_02_BAD_text_trauma",
        "BAD",
    ),  # "CRITICAL TRAUMA HIGHWAY" + Fix Monitor
    (24.0, 25.0, "seg_03_bridge_good", "GOOD"),
    (
        25.0,
        29.0,
        "seg_04_BAD_text_sw1_tiltrotor",
        "BAD",
    ),  # "SW-1" + Replace grey/yellow tilt-rotor
    (29.0, 35.0, "seg_05_pre_takeoff_good", "GOOD"),
    (
        35.0,
        40.0,
        "seg_06_BAD_replace_white_drone",
        "BAD",
    ),  # Replace small white drone (takeoff)
    (40.0, 41.0, "seg_07_transition_good", "GOOD"),
    (
        41.0,
        45.0,
        "seg_08_BAD_replace_quadcopter",
        "BAD",
    ),  # Replace white consumer quad (traffic)
    (45.0, 51.0, "seg_09_flight_good", "GOOD"),  # 0:46 is already correct drone
    (
        51.0,
        55.0,
        "seg_10_BAD_vitals_text_fixedwing",
        "BAD",
    ),  # Fix Vitals Text + Replace orange fixed-wing
    (55.0, 56.0, "seg_11_transition_good", "GOOD"),
    (
        56.0,
        60.0,
        "seg_12_BAD_replace_white_jet",
        "BAD",
    ),  # Replace massive white jet (descent)
    (60.0, 61.0, "seg_13_transition_good", "GOOD"),
    (61.0, 65.0, "seg_14_BAD_replace_blue_quad", "BAD"),  # Replace blue quad (landing)
    (65.0, 76.0, "seg_15_surgeon_landing_good", "GOOD"),
    (
        76.0,
        80.0,
        "seg_16_BAD_text_flight_time",
        "BAD",
    ),  # "FLIGHT TIME IN MINUTES" or "ETA"
    (80.0, 81.0, "seg_17_transition_good", "GOOD"),
    (81.0, 85.0, "seg_18_BAD_text_sw1_alpha", "BAD"),  # "SW-1 ALPHA" (no ALPFGE)
    (85.0, 95.0, "seg_19_outro_credits_good", "GOOD"),
]

# Exact correction prompts for the Parallel Refinement
BAD_PROMPTS = {
    "seg_02_BAD_text_trauma": f"Cinematic medium shot. Emergency dispatch center. Correct the typo 'CRITICAL TRAMUA HIGHWAY' to exactly 'CRITICAL TRAUMA HIGHWAY'. Background monitors must show clean readable medical charts only, no gibberish text.{SHARED_STYLE}",
    "seg_04_BAD_text_sw1_tiltrotor": f"Photorealistic cinematic. Replace grey/yellow tilt-rotor with {DRONE_SPEC}. Correct wrong label 'SLLAO' so chassis text reads exactly 'SW-1'. Night helipad setting.{SHARED_STYLE}",
    "seg_06_BAD_replace_white_drone": f"Photorealistic cinematic takeoff shot. Replace the small white drone with {DRONE_SPEC}. Powerful downwash pushing dust on hospital rooftop.{SHARED_STYLE}",
    "seg_08_BAD_replace_quadcopter": f"Cinematic aerial wide shot. Replace white consumer quadcopter with {DRONE_SPEC}. Flying above gridlocked highway traffic at night.{SHARED_STYLE}",
    "seg_10_BAD_vitals_text_fixedwing": f"High-tech medical HUD. Replace orange/yellow fixed-wing aircraft in center with {DRONE_SPEC}. Correct text exactly: 'Patient Name', '90 bpm', 'SpO2%', 'Heart Rate' and remove wrong text like 'Kisszach', '900 peem', 'SpO%', 'Resrt Rate'.{SHARED_STYLE}",
    "seg_12_BAD_replace_white_jet": f"Photorealistic cinematic descent shot. Replace the massive white jet with {DRONE_SPEC} coming in for landing on rooftop helipad.{SHARED_STYLE}",
    "seg_14_BAD_replace_blue_quad": f"Photorealistic cinematic landing shot. Replace blue quadcopter with {DRONE_SPEC} touching down on the red H pad center.{SHARED_STYLE}",
    "seg_16_BAD_text_flight_time": f"Cinematic infographic comparison. Replace wrong text 'W BAP LITA MINUTES' with correct readable text: 'FLIGHT TIME IN MINUTES' and 'ETA'. No gibberish text.{SHARED_STYLE}",
    "seg_18_BAD_text_sw1_alpha": f"Cinematic end title card on deep navy. Flat silhouette of SW-1 Alpha octocopter. Correct wrong text 'SW-1 ALPFGE' to exactly 'SW-1 ALPHA'. Centered white text only, no gibberish.{SHARED_STYLE}",
}
# ────────────────────────────────────────────────────────────────────────────────


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


def cut_segment(ffmpeg_bin, src, start, end, dest):
    duration = end - start
    cmd = [
        ffmpeg_bin,
        "-y",
        "-ss",
        str(start),
        "-i",
        src,
        "-t",
        str(duration),
        "-c",
        "copy",
        "-avoid_negative_ts",
        "make_zero",
        dest,
    ]
    return subprocess.run(cmd, capture_output=True).returncode == 0


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except:
            pass

    print(
        "=" * 60 + "\n  SW-1 Alpha -- Surgical Splitter (2024 Final Spec)\n" + "=" * 60
    )
    ffmpeg_bin = find_ffmpeg()
    if not ffmpeg_bin:
        print("ERROR: FFMPEG not found! Please install ffmpeg or add it to PATH.")
        sys.exit(1)

    os.makedirs(GOOD_DIR, exist_ok=True)
    os.makedirs(BAD_DIR, exist_ok=True)

    plan = []
    print(f"  Source: {INPUT_VIDEO}\n")
    for i, (start, end, label, seg_type) in enumerate(SEGMENTS):
        out_dir = BAD_DIR if seg_type == "BAD" else GOOD_DIR
        out_path = os.path.join(out_dir, f"{label}.mp4")
        type_str = "[BAD]" if seg_type == "BAD" else "[GOOD]"
        print(
            f"  [{i + 1}/{len(SEGMENTS)}] {type_str:6s} {start:4.1f}s -> {end:4.1f}s | {label}"
        )

        success = cut_segment(ffmpeg_bin, INPUT_VIDEO, start, end, out_path)
        entry = {
            "index": i + 1,
            "label": label,
            "type": seg_type,
            "start": start,
            "end": end,
            "path": out_path,
            "status": "ready" if success else "error",
        }
        if seg_type == "BAD":
            entry["v2v_prompt"] = BAD_PROMPTS.get(
                label, "Photorealistic cinematic medical drone."
            )
        plan.append(entry)

    with open(PLAN_FILE, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)
    print(f"\nSUCCESS: Created {len(plan)} segments. Plan saved to segment_plan.json.")


if __name__ == "__main__":
    main()
