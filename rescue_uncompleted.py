import subprocess
import json
import time

variants = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
existing = {
    "A": 396217,
    "B": 396227,
    "C": 396228,
    "D": 396226,
    "E": 396229,
    "F": 396230,
    "G": 396223,
    "J": 396218
}

for var in variants:
    print(f"--- Launching {var} ---")
    if var in existing:
        cmd = [
            "jl", "run", "wan_pipeline_v2.py",
            "--requirements", "requirements_v2.txt",
            "--on", str(existing[var]),
            "--", "--variant", var
        ]
    else:
        # H and I missing, trying A6000 or RTX6000Ada
        cmd = [
            "jl", "run", "wan_pipeline_v2.py",
            "--requirements", "requirements_v2.txt",
            "--gpu", "A6000", # We'll try A6000 for the last two
            "--storage", "300",
            "--name", f"sw1-{var}-a6000",
            "--keep", "--yes",
            "--", "--variant", var
        ]
        
    print(f"Running: {' '.join(cmd)}")
    log_file = open(f"logs/variant_{var}.log", "w")
    proc = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)
    time.sleep(2)
