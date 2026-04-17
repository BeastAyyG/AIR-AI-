"""
SW-1 Alpha — Emergency Video Rescue Script
Connects to each old instance, finds the final MP4, uploads to transfer.sh.
Run: python rescue_videos.py
"""
import os, subprocess, sys, time

API_KEY = "mgMHYQlRZqsDXo988uk1Ux4uzRxTeXAxScvRNU3QTgA"
env = os.environ.copy()
env["JL_API_KEY"] = API_KEY

# First batch instance IDs mapped to variant
INSTANCES = {
    "A": "396155",
    "B": "396156",
    "E": "396158",
    "F": "396159",
    "J": "396165",
    "C": "396168",
    "D": "396169",
    "I": "396171",
    "H": "396173",
    "G": "396174",
}

STYLES = {
    "A": "Standard_Night",    "B": "Monsoon_Storm",
    "C": "Golden_Hour_Dawn",  "D": "Neon_Cyberpunk",
    "E": "Handheld_Documentary", "F": "Arctic_Blizzard",
    "G": "Desert_Afternoon",  "H": "IMAX_Documentary",
    "I": "Film_Noir_BW",      "J": "Anime_Stylized",
}

# The upload-and-print script to run on each remote machine
REMOTE_SCRIPT = """
import os, subprocess, glob

# Find the final stitched MP4
finals = glob.glob('/home/variant_*/FINAL_SW1_VARIANT_*.mp4')
if not finals:
    # Try alternative paths
    finals = glob.glob('/home/FINAL_SW1_VARIANT_*.mp4')
if not finals:
    finals = glob.glob('/tmp/FINAL_SW1_VARIANT_*.mp4')
if not finals:
    # List what exists
    for root, dirs, files in os.walk('/home'):
        for f in files:
            if f.endswith('.mp4'):
                print(f'FOUND_MP4: {os.path.join(root, f)}')
    print('NO_FINAL_FOUND')
else:
    for fpath in finals:
        fname = os.path.basename(fpath)
        print(f'UPLOADING: {fpath}')
        result = subprocess.run(
            ['curl', '--upload-file', fpath, f'https://transfer.sh/{fname}'],
            capture_output=True, text=True, timeout=600
        )
        url = result.stdout.strip()
        print(f'DOWNLOAD_URL: {url}')
        print(f'STDERR: {result.stderr[:200]}')
"""

print()
print("=" * 60)
print("  SW-1 ALPHA — EMERGENCY VIDEO RESCUE")
print("=" * 60)
print(f"  Checking {len(INSTANCES)} instances for saved videos...\n")

download_urls = {}

for variant, instance_id in INSTANCES.items():
    style = STYLES[variant]
    print(f"\n[{variant}] {style} — Instance {instance_id}")
    print(f"    Running remote scan...")

    # Execute the rescue script remotely via jl run --on
    cmd = [
        sys.executable, "-c",
        f"""
import sys, os
os.environ['JL_API_KEY'] = '{API_KEY}'
from jarvislabs.cli.app import main
sys.argv = ['jl', 'run', '--on', '{instance_id}',
    '--yes', '--',
    'python3', '-c', {repr(REMOTE_SCRIPT)}]
main()
"""
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True,
            timeout=700,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        output = result.stdout + result.stderr

        # Parse output
        url = None
        found_mp4s = []
        for line in output.splitlines():
            if "DOWNLOAD_URL:" in line:
                url = line.split("DOWNLOAD_URL:")[-1].strip()
                if url.startswith("http"):
                    download_urls[variant] = url
                    print(f"    >>> DOWNLOAD URL: {url}")
            elif "FOUND_MP4:" in line:
                found_mp4s.append(line.split("FOUND_MP4:")[-1].strip())
                print(f"    Found file: {line.split('FOUND_MP4:')[-1].strip()}")
            elif "UPLOADING:" in line:
                print(f"    Uploading: {line.split('UPLOADING:')[-1].strip()}")
            elif "NO_FINAL_FOUND" in line:
                print(f"    [!] No final MP4 found on this instance")

        if not url and not found_mp4s:
            print(f"    [!] Could not retrieve — raw output:")
            print(f"    {output[:400]}")

    except subprocess.TimeoutExpired:
        print(f"    [!] Timeout on instance {instance_id}")
    except Exception as e:
        print(f"    [!] Error: {e}")

# Final summary
print()
print("=" * 60)
print("  RESCUE COMPLETE — DOWNLOAD URLS")
print("=" * 60)
if download_urls:
    for var, url in download_urls.items():
        print(f"  [{var}] {STYLES[var]}")
        print(f"        {url}")
        print()
    # Save to file
    with open("rescued_download_urls.txt", "w") as f:
        f.write("SW-1 Alpha — Rescued Video Download URLs\n")
        f.write("=" * 50 + "\n\n")
        for var, url in download_urls.items():
            f.write(f"[{var}] {STYLES[var]}\n{url}\n\n")
    print(f"  Saved to: rescued_download_urls.txt")
else:
    print("  No URLs recovered. Instances may still be rendering.")
print("=" * 60)
