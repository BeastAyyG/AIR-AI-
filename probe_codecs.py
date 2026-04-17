import subprocess, json, os

def probe(f):
    if not os.path.exists(f):
        return "MISSING"
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", f],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        return "ERROR: " + r.stderr[:80]
    d = json.loads(r.stdout)
    out = []
    for s in d.get("streams", []):
        out.append(f"{s.get('codec_name','?')} {s.get('width','?')}x{s.get('height','?')} fps={s.get('r_frame_rate','?')}")
    return " | ".join(out) if out else "no streams"

files = [
    r"C:\happy horse\ALL_VIDEOS\FINAL_WAN22_MOVIE.mp4",
    r"C:\happy horse\ALL_VIDEOS\GOOD_SEGMENTS\seg_01_intro_accident.mp4",
    r"C:\happy horse\ALL_VIDEOS\BAD_SEGMENTS\seg_02_BAD_text_trauma.mp4",
    r"C:\happy horse\ALL_VIDEOS\BAD_SEGMENTS\seg_02_BAD_text_trauma_REFINED.mp4",
    r"C:\happy horse\ALL_VIDEOS\BAD_SEGMENTS\seg_04_BAD_text_sw1_tiltrotor_REFINED.mp4",
    r"C:\happy horse\ALL_VIDEOS\BAD_SEGMENTS\seg_06_BAD_replace_white_drone_REFINED.mp4",
    r"C:\happy horse\ALL_VIDEOS\BAD_SEGMENTS\seg_08_BAD_replace_quadcopter_REFINED.mp4",
    r"C:\happy horse\ALL_VIDEOS\BAD_SEGMENTS\seg_10_BAD_vitals_text_fixedwing_REFINED.mp4",
    r"C:\happy horse\ALL_VIDEOS\BAD_SEGMENTS\seg_12_BAD_replace_white_jet_REFINED.mp4",
    r"C:\happy horse\ALL_VIDEOS\BAD_SEGMENTS\seg_14_BAD_replace_blue_quad_REFINED.mp4",
    r"C:\happy horse\ALL_VIDEOS\BAD_SEGMENTS\seg_16_BAD_text_flight_time_REFINED.mp4",
    r"C:\happy horse\ALL_VIDEOS\BAD_SEGMENTS\seg_18_BAD_text_sw1_alpha.mp4",
]

print("=== CODEC COMPATIBILITY AUDIT ===")
codecs = []
for f in files:
    name = os.path.basename(f)
    info = probe(f)
    print(f"  {name}")
    print(f"    -> {info}")
    codecs.append(info)

# Check if all match
unique = set(c for c in codecs if c not in ("MISSING", "no streams"))
print()
if len(unique) == 1:
    print("ALL CODECS MATCH - safe to use -c copy (lossless join)")
else:
    print("CODEC MISMATCH DETECTED - must re-encode during join")
    for i, (f, c) in enumerate(zip(files, codecs)):
        print(f"  [{i}] {os.path.basename(f)}: {c}")
