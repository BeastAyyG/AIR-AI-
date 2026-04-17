#!/usr/bin/env python3
"""
Coordinate calibration tool.
Draws a pixel grid on specific frames so we can read exact coordinates.
"""
import subprocess, os, sys

INPUT  = r"C:\happy horse\ALL_VIDEOS\FINAL_WAN22_MOVIE.mp4"
OUT    = r"C:\happy horse\ALL_VIDEOS\PROBLEM_FRAMES"
FONT   = "C\\:/Windows/Fonts/arialbd.ttf"

def extract_with_grid(ts, label, grid_color="white@0.3"):
    """Extract a frame with 100px grid lines and coordinate labels."""
    out_path = os.path.join(OUT, f"{label}_GRID.png")
    # Draw horizontal lines every 100px, vertical lines every 100px
    # Also draw text labels at each intersection
    
    h_lines = ""
    for y in range(0, 721, 100):
        h_lines += f"drawbox=x=0:y={y}:w=1280:h=1:color={grid_color}:t=fill,"
        h_lines += f"drawtext=fontfile='{FONT}':text='y={y}':fontcolor=yellow:fontsize=14:x=5:y={y+2},"
    
    v_lines = ""
    for x in range(0, 1281, 100):
        v_lines += f"drawbox=x={x}:y=0:w=1:h=720:color={grid_color}:t=fill,"
        # Add x labels at top
        v_lines += f"drawtext=fontfile='{FONT}':text='x={x}':fontcolor=yellow:fontsize=12:x={x+2}:y=2,"
    
    filtergraph = h_lines + v_lines.rstrip(",")
    
    filter_file = r"C:\TEMP_SW1\grid_filter.txt"
    os.makedirs(r"C:\TEMP_SW1", exist_ok=True)
    with open(filter_file, "w") as f:
        f.write(filtergraph)
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(ts),
        "-i", INPUT,
        "-frames:v", "1",
        "-filter_script:v", filter_file,
        "-q:v", "1",
        out_path
    ]
    r = subprocess.run(cmd, capture_output=True)
    if os.path.exists(out_path):
        kb = os.path.getsize(out_path) // 1024
        print(f"  OK ({kb} KB) -> {os.path.basename(out_path)}")
    else:
        print(f"  FAILED: {r.stderr.decode()[-200:]}")

print("Generating calibration grids...")
frames = [
    (20.5, "0m20_trauma_banner"),
    (53.0, "0m53_vitals"),
    (77.0, "1m16_flight_time"),
    (82.0, "1m21_sw1_alpha"),
]
for ts, label in frames:
    extract_with_grid(ts, label)
print("Done - open PROBLEM_FRAMES to read exact coordinates")
