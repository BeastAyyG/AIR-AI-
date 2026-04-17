import argparse
import json
import os
import shlex
import subprocess
import sys

ROOT = r"C:\happy horse"
JL = os.path.join(ROOT, "manage_jl.py")
REQ = os.path.join(ROOT, "STAGING_AREA", "requirements_refine.txt")
REFINE = os.path.join(ROOT, "STAGING_AREA", "refine_drone_video.py")


def run(cmd, check=True):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    p = subprocess.run(cmd, text=True, capture_output=True, env=env)
    if check and p.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
        )
    return p


def jl(*args, check=True):
    return run([sys.executable, JL, *args], check=check)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--prompt", required=True)
    args = ap.parse_args()

    label = args.label
    input_local = os.path.join(
        ROOT, "STAGING_AREA", "ALL_VIDEOS", "BAD_SEGMENTS", f"{label}.mp4"
    )
    run_log = os.path.join(ROOT, "STAGING_AREA", "logs", f"debug_run_{label}.log")
    pip_log = os.path.join(ROOT, "STAGING_AREA", "logs", f"debug_pip_{label}.log")
    out_debug = os.path.join(
        ROOT, "STAGING_AREA", "ALL_VIDEOS", "BAD_SEGMENTS", f"{label}_REFINED_DEBUG.mp4"
    )

    if not os.path.exists(input_local):
        raise FileNotFoundError(input_local)

    create = jl(
        "create",
        "--gpu",
        "H100",
        "--region",
        "IN2",
        "--storage",
        "100",
        "--name",
        f"debug-{label[:40]}",
        "--yes",
        "--json",
    ).stdout
    mid = str(json.loads(create)["machine_id"])
    print(f"MID={mid}")

    try:
        jl("upload", mid, REQ, "/home/requirements_refine.txt")
        jl("upload", mid, REFINE, "/home/refine_drone_video.py")
        jl("upload", mid, input_local, f"/home/{label}.mp4")

        cmd = (
            "python -m pip install -r /home/requirements_refine.txt > /home/pip.log 2>&1; "
            "python /home/refine_drone_video.py "
            f"--input_video /home/{label}.mp4 "
            f"--output_video /home/{label}_REFINED.mp4 "
            f"--prompt {shlex.quote(args.prompt)} "
            "--strength 0.40 --steps 30 --num_versions 1 > /home/run.log 2>&1; "
            "echo rc:$?"
        )
        jl("exec", mid, "--", "bash", "-lc", cmd, check=False)
        jl("download", mid, "/home/pip.log", pip_log, check=False)
        jl("download", mid, "/home/run.log", run_log, check=False)
        jl("download", mid, f"/home/{label}_REFINED.mp4", out_debug, check=False)
    finally:
        jl("destroy", "-y", mid, check=False)


if __name__ == "__main__":
    main()
