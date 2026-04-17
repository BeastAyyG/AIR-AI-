"""
SW-1 Alpha — Download all 10 variant videos from JarvisLabs saved runs.
Run: python download_variants.py
"""
import os, subprocess, sys
from pathlib import Path

API_KEY = "mgMHYQlRZqsDXo988uk1Ux4uzRxTeXAxScvRNU3QTgA"

RUN_IDS = {
    "A": ("r_44e833d7", "Standard_Night"),
    "B": ("r_522c2591", "Monsoon_Storm"),
    "E": ("r_d570e3dd", "Handheld_Documentary"),
    "F": ("r_76e51e69", "Arctic_Blizzard"),
    "J": ("r_466f954d", "Anime_Stylized"),
    "C": ("r_584ef55e", "Golden_Hour_Dawn"),
    "D": ("r_e7c789c7", "Neon_Cyberpunk"),
    "I": ("r_8a8fce05", "Film_Noir_BW"),
    "H": ("r_431be14a", "IMAX_Documentary"),
    "G": ("r_23393e74", "Desert_Afternoon"),
}

OUT_DIR = Path(__file__).parent / "SW1_ALPHA_VIDEOS"
OUT_DIR.mkdir(exist_ok=True)

env = os.environ.copy()
env["JL_API_KEY"] = API_KEY

print("\n" + "="*60)
print("  SW-1 ALPHA — DOWNLOADING ALL 10 VARIANTS")
print("="*60)
print(f"  Output folder: {OUT_DIR}\n")

for var, (run_id, style) in RUN_IDS.items():
    dest = OUT_DIR / f"Variant_{var}_{style}"
    dest.mkdir(exist_ok=True)
    print(f"[{var}] {style} ({run_id}) → Downloading...")
    result = subprocess.run(
        ["jl", "run", "download", run_id, "--output", str(dest)],
        env=env, capture_output=True, text=True
    )
    if result.returncode == 0 or "download" in result.stdout.lower():
        print(f"    OK  → {dest}")
    else:
        print(f"    Output: {result.stdout.strip()}")
        print(f"    Stderr: {result.stderr.strip()[:200]}")

print("\n" + "="*60)
print("  DOWNLOAD COMPLETE — check SW1_ALPHA_VIDEOS/ folder")
print("="*60)
