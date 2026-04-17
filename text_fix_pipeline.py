#!/usr/bin/env python3
"""
SW-1 Alpha — Precision Text Fix (Calibrated)
Coordinates determined from pixel-grid analysis of extracted frames.
"""
import subprocess, os, sys, shutil

INPUT        = r"C:\happy horse\ALL_VIDEOS\FINAL_WAN22_MOVIE.mp4"
TEMP_OUT     = r"C:\TEMP_SW1\TEXT_FIXED_v2.mp4"
FINAL_OUT    = r"C:\happy horse\ALL_VIDEOS\TEXT_FIXED_MOVIE.mp4"
FILTER_FILE  = r"C:\TEMP_SW1\filters_v2.txt"
FONT         = "C\\:/Windows/Fonts/arialbd.ttf"

os.makedirs(r"C:\TEMP_SW1", exist_ok=True)


def build_filters():
    """Build filtergraph with calibrated pixel coordinates."""
    # Colors in 0xAARRGGBB (AA=FF fully opaque, AA=CC semi-transparent)
    RED_BANNER   = "0xFFC61A1A"   # Dark red matching ribbon
    DARK_BLUE    = "0xFF0A1E30"   # Dark navy for vitals panel
    TEAL_BADGE   = "0xFF104E6A"   # Dark teal matching flight badge
    DARK_NAV     = "0xFF010A18"   # Very dark navy for SW-1 end title

    lines = []

    # ─── FIX 1: "CRITICAL TRAMUA HIGHWAY" -> "CRITICAL TRAUMA HIGHWAY" ───────
    # Grid shows: Banner ribbon at y=50-100, x=530-1060
    # Cover the text portion of the ribbon with matching red, draw correct text
    lines.extend([
        f"drawbox=x=490:y=45:w=590:h=62:color={RED_BANNER}:t=fill:enable='between(t,20,24)',",
        f"drawtext=fontfile='{FONT}'",
        ":text='CRITICAL TRAUMA HIGHWAY'",
        ":fontcolor=white:fontsize=24",
        ":x=(w-text_w)/2+150:y=63",
        ":enable='between(t,20,24)',",
    ])

    # ─── FIX 2: Sidebar gibberish (FRIOLME, ROTY, ANICXUAME, ROLAE) ──────────
    # Grid shows: Sidebar text x=185-310, y=310-405
    lines.extend([
        f"drawbox=x=183:y=308:w=135:h=105:color=0xCC1A0A00:t=fill:enable='between(t,20,24)',",
    ])

    # ─── FIX 3a: "Kisszazch" -> "Patient Name" ───────────────────────────────
    # Grid shows: "Kisszazch" text at x=930-1130, y=388-412
    lines.extend([
        f"drawbox=x=925:y=385:w=215:h=35:color={DARK_BLUE}:t=fill:enable='between(t,51,55)',",
        f"drawtext=fontfile='{FONT}'",
        ":text='Patient Name'",
        ":fontcolor=white:fontsize=19",
        ":x=932:y=390",
        ":enable='between(t,51,55)',",
    ])

    # ─── FIX 3b: "SOO peent" -> "90 bpm" ─────────────────────────────────────
    # Grid shows: box at x=960-1130, y=465-510
    lines.extend([
        f"drawbox=x=958:y=462:w=175:h=52:color={DARK_BLUE}:t=fill:enable='between(t,51,55)',",
        f"drawtext=fontfile='{FONT}'",
        ":text='90 bpm'",
        ":fontcolor=white:fontsize=22",
        ":x=965:y=472",
        ":enable='between(t,51,55)',",
    ])

    # ─── FIX 3c: "SpO%" -> "SpO2%" and "Resrt Rate" -> "Heart Rate" ──────────
    # Grid shows: labels at x=960-1130, y=505-530
    lines.extend([
        f"drawbox=x=958:y=503:w=175:h=35:color={DARK_BLUE}:t=fill:enable='between(t,51,55)',",
        f"drawtext=fontfile='{FONT}'",
        ":text='SpO2%'",
        ":fontcolor=white:fontsize=16",
        ":x=965:y=510",
        ":enable='between(t,51,55)',",
        f"drawtext=fontfile='{FONT}'",
        ":text='Heart Rate'",
        ":fontcolor=white:fontsize=16",
        ":x=1050:y=510",
        ":enable='between(t,51,55)',",
    ])

    # ─── FIX 4: "W BAP LITA" -> "FLIGHT TIME" ───────────────────────────────
    # Grid shows: banner badge at x=865-1130, y=370-415 (w=265, h=45)
    # Use same teal color as badge background
    lines.extend([
        f"drawbox=x=862:y=368:w=275:h=48:color={TEAL_BADGE}:t=fill:enable='between(t,76,80)',",
        f"drawtext=fontfile='{FONT}'",
        ":text='FLIGHT TIME'",
        ":fontcolor=white:fontsize=17",
        ":x=880:y=374",
        ":enable='between(t,76,80)',",
        f"drawtext=fontfile='{FONT}'",
        ":text='MINUTES'",
        ":fontcolor=white:fontsize=22",
        ":x=910:y=393",
        ":enable='between(t,76,80)',",
    ])

    # ─── FIX 5: "SW-1 ALPFGE" -> "SW-1 ALPHA" ───────────────────────────────
    # Grid shows: text at x=555-750, y=393-420 (center of frame x=640)
    lines.extend([
        f"drawbox=x=540:y=388:w=220:h=38:color={DARK_NAV}:t=fill:enable='between(t,81,85)',",
        f"drawtext=fontfile='{FONT}'",
        ":text='SW-1 ALPHA'",
        ":fontcolor=white:fontsize=26",
        ":x=(w-text_w)/2:y=394",
        ":enable='between(t,81,85)'",
    ])

    content = "\n".join(lines)
    with open(FILTER_FILE, "w", encoding="ascii") as f:
        f.write(content)


def find_ffmpeg():
    for c in ["ffmpeg", r"C:\ffmpeg\bin\ffmpeg.exe"]:
        try:
            if subprocess.run([c, "-version"], capture_output=True).returncode == 0:
                return c
        except: pass
    return None


def main():
    print("=" * 65)
    print("  SW-1 Alpha — Precision Text Fix v2 (Calibrated Coordinates)")
    print("=" * 65)

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        print("ERROR: ffmpeg not found"); sys.exit(1)

    build_filters()
    print(f"  filter file:  {FILTER_FILE}")
    print(f"  input:        {INPUT}")
    print(f"  final output: {FINAL_OUT}")
    print(f"\nProcessing all corrections...")

    cmd = [
        ffmpeg, "-y",
        "-i", INPUT,
        "-filter_script:v", FILTER_FILE,
        "-c:v", "libx264",
        "-crf", "15",
        "-preset", "medium",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        TEMP_OUT,
    ]

    result = subprocess.run(
        cmd, capture_output=True,
        text=True, encoding="utf-8", errors="replace"
    )

    if result.returncode == 0:
        shutil.copy2(TEMP_OUT, FINAL_OUT)
        mb = os.path.getsize(FINAL_OUT) / (1024*1024)
        print(f"\n{'='*65}")
        print(f"  SUCCESS!")
        print(f"  Output: {FINAL_OUT}")
        print(f"  Size:   {mb:.1f} MB  |  1280x720 @ 16fps  |  H.264 CRF 15")
        print(f"\n  Corrections applied:")
        print(f"  [OK] 0:20-0:24  CRITICAL TRAUMA HIGHWAY")
        print(f"  [OK] 0:20-0:24  Sidebar gibberish covered")
        print(f"  [OK] 0:51-0:55  Patient Name / 90 bpm / SpO2% / Heart Rate")
        print(f"  [OK] 1:16-1:20  FLIGHT TIME MINUTES")
        print(f"  [OK] 1:21-1:25  SW-1 ALPHA")
        print(f"\n  Drone morphing (0:25, 0:35, 0:41, 0:56, 1:01)")
        print(f"  -> Requires JarvisLabs GPU (Wan 2.2, separate step)")
        print(f"{'='*65}")
    else:
        err_lines = [l for l in result.stderr.split("\n") if l.strip()][-15:]
        for l in err_lines:
            print(l)
        with open(r"C:\TEMP_SW1\error_v2.log", "w") as f:
            f.write(result.stderr)
        print(f"\nFull error saved: C:\\TEMP_SW1\\error_v2.log")
        sys.exit(1)


if __name__ == "__main__":
    main()
