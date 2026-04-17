#!/usr/bin/env python3
"""
SW-1 Alpha — Smart Rejoiner
============================
Handles the codec mismatch between GOOD segments (1280x720 @ 16fps)
and REFINED segments (720x480 @ 8fps) by upscaling REFINED files first,
then stitching everything together in order.

Usage: python smart_rejoin.py
Output: C:\happy horse\ALL_VIDEOS\REJOINED_FINAL_MOVIE.mp4
"""

import os
import json
import subprocess
import sys
import shutil

# ─── CONFIG ────────────────────────────────────────────────────────────────────
PLAN_FILE    = r"C:\happy horse\ALL_VIDEOS\segment_plan.json"
BAD_DIR      = r"C:\happy horse\ALL_VIDEOS\BAD_SEGMENTS"
GOOD_DIR     = r"C:\happy horse\ALL_VIDEOS\GOOD_SEGMENTS"
UPSCALED_DIR = r"C:\happy horse\ALL_VIDEOS\UPSCALED_REFINED"
LIST_FILE    = r"C:\happy horse\ALL_VIDEOS\concat_list.txt"
OUTPUT_MOVIE = r"C:\happy horse\ALL_VIDEOS\REJOINED_FINAL_MOVIE.mp4"

# Target spec: match original FINAL_WAN22_MOVIE.mp4
TARGET_W    = 1280
TARGET_H    = 720
TARGET_FPS  = 16
TARGET_CRF  = 18    # High quality H.264 (lower = better, 18 ≈ visually lossless)
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
        except Exception:
            continue
    return None


def probe_video(ffmpeg_bin, path):
    """Return (width, height, fps_str) or None."""
    ffprobe = ffmpeg_bin.replace("ffmpeg", "ffprobe")
    if not os.path.exists(ffprobe):
        ffprobe = "ffprobe"
    r = subprocess.run(
        [ffprobe, "-v", "quiet", "-print_format", "json", "-show_streams", path],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        return None
    try:
        d = json.loads(r.stdout)
        for s in d.get("streams", []):
            if s.get("codec_type") == "video":
                return int(s.get("width", 0)), int(s.get("height", 0)), s.get("r_frame_rate", "?")
    except Exception:
        pass
    return None


def needs_upscale(ffmpeg_bin, path):
    info = probe_video(ffmpeg_bin, path)
    if info is None:
        return False
    w, h, fps = info
    if w == TARGET_W and h == TARGET_H and fps == f"{TARGET_FPS}/1":
        return False
    return True


def upscale_segment(ffmpeg_bin, src, dst):
    """Upscale src to TARGET_W x TARGET_H @ TARGET_FPS using high-quality H.264."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    cmd = [
        ffmpeg_bin, "-y",
        "-i", src,
        "-vf", f"scale={TARGET_W}:{TARGET_H}:flags=lanczos,fps={TARGET_FPS}",
        "-c:v", "libx264",
        "-crf", str(TARGET_CRF),
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-an",   # No audio track (refined segments have none)
        dst,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, r.stderr[-300:] if r.returncode != 0 else ""


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("=" * 60)
    print("  SW-1 Alpha -- Smart Video Rejoiner")
    print("=" * 60)

    ffmpeg_bin = find_ffmpeg()
    if not ffmpeg_bin:
        print("ERROR: ffmpeg not found. Install via: choco install ffmpeg")
        sys.exit(1)
    print(f"  ffmpeg: {ffmpeg_bin}")

    if not os.path.exists(PLAN_FILE):
        print(f"ERROR: Segment plan not found: {PLAN_FILE}")
        sys.exit(1)

    with open(PLAN_FILE, "r", encoding="utf-8") as f:
        plan = json.load(f)

    os.makedirs(UPSCALED_DIR, exist_ok=True)

    print(f"\nTarget spec: {TARGET_W}x{TARGET_H} @ {TARGET_FPS}fps (H.264 CRF {TARGET_CRF})")
    print("\n--- Phase 1: Upscaling REFINED segments ---")

    # Process each segment: pick the best version and upscale if needed
    segment_files = []
    all_ok = True

    for seg in plan:
        label    = seg["label"]
        seg_type = seg["type"]
        orig_path = seg["path"]

        if seg_type == "BAD":
            refined_path = orig_path.replace(".mp4", "_REFINED.mp4")
            if os.path.exists(refined_path) and os.path.getsize(refined_path) > 10000:
                chosen = refined_path
                tag = "[REFINED]"
            else:
                chosen = orig_path
                tag = "[ORIGINAL fallback]"
                if not os.path.exists(orig_path):
                    print(f"  ERROR: {label} — neither REFINED nor original found!")
                    all_ok = False
                    continue
        else:
            chosen = orig_path
            tag = "[GOOD]"

        # Check if upscale is needed
        if needs_upscale(ffmpeg_bin, chosen):
            upscaled_path = os.path.join(UPSCALED_DIR, f"{label}.mp4")
            info = probe_video(ffmpeg_bin, chosen)
            print(f"  Upscaling {label} {info[0]}x{info[1]} @ {info[2]} -> {TARGET_W}x{TARGET_H} @ {TARGET_FPS}fps ...")
            ok, err = upscale_segment(ffmpeg_bin, chosen, upscaled_path)
            if ok:
                segment_files.append((label, upscaled_path, tag + " [upscaled]"))
                print(f"    OK -> {os.path.basename(upscaled_path)}")
            else:
                print(f"    FAILED: {err}")
                print(f"    Falling back to original for {label}")
                segment_files.append((label, chosen, tag + " [upscale failed]"))
                all_ok = False
        else:
            segment_files.append((label, chosen, tag))
            info = probe_video(ffmpeg_bin, chosen)
            print(f"  OK (no upscale needed): {label} {info}")

    print(f"\n  {len(segment_files)}/{len(plan)} segments ready.")

    print("\n--- Phase 2: Building concat list ---")
    with open(LIST_FILE, "w", encoding="utf-8") as f:
        for label, path, tag in segment_files:
            escaped = path.replace("\\", "/")
            f.write(f"file '{escaped}'\n")
            print(f"  {tag:30s} {os.path.basename(path)}")

    print("\n--- Phase 3: Joining final movie ---")
    cmd = [
        ffmpeg_bin, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", LIST_FILE,
        "-c:v", "libx264",
        "-crf", str(TARGET_CRF),
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-r", str(TARGET_FPS),
        "-vf", f"scale={TARGET_W}:{TARGET_H}",
        OUTPUT_MOVIE,
    ]
    print(f"  Running ffmpeg concat re-encode...")
    r = subprocess.run(cmd, capture_output=True, text=True)

    if r.returncode == 0:
        size_mb = os.path.getsize(OUTPUT_MOVIE) / (1024 * 1024)
        print(f"\n{'='*60}")
        print(f"  SUCCESS! Final movie saved:")
        print(f"  {OUTPUT_MOVIE}")
        print(f"  Size: {size_mb:.1f} MB")
        print(f"  Spec: {TARGET_W}x{TARGET_H} @ {TARGET_FPS}fps, CRF {TARGET_CRF}")
        if not all_ok:
            print(f"\n  NOTE: Some segments used fallback/original. Review log above.")
        print(f"{'='*60}")
    else:
        print(f"\nERROR joining video:\n{r.stderr[-800:]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
