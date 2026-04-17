#!/usr/bin/env python3
"""
SW-1 Alpha - Parallel Stage Refiner (robust mode)

What this script does:
1) Creates one H100 instance per BAD segment.
2) Uploads refine script, segment video, and requirements to each instance.
3) Executes refinement remotely with fast defaults (1 version, 30 steps).
4) Downloads *_REFINED.mp4 back to STAGING_AREA and ALL_VIDEOS.
5) Destroys instances to stop billing.
"""

import json
import os
import shlex
import subprocess
import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = "mgMHYQlRZqsDXo988uk1Ux4uzRxTeXAxScvRNU3QTgA"
ROOT = r"C:\happy horse"
STAGING_ROOT = os.path.join(ROOT, "STAGING_AREA")
PLAN_FILE = os.path.join(STAGING_ROOT, "ALL_VIDEOS", "segment_plan.json")
LOCAL_PLAN_MIRROR = os.path.join(ROOT, "ALL_VIDEOS", "segment_plan.json")

REFINE_SCRIPT_NAME = "refine_drone_video.py"
REFINE_SCRIPT_PATH = os.path.join(STAGING_ROOT, REFINE_SCRIPT_NAME)
REQUIREMENTS_FILE = os.path.join(STAGING_ROOT, "requirements_refine.txt")

GPU_TYPE = "H100"
GPU_REGION = "IN2"
STORAGE_GB = 100
MAX_WORKERS = 9
STAGGER_SECONDS = 2
MAX_SEGMENT_ATTEMPTS = 2

# Fast mode for your deadline
DEFAULT_STRENGTH = "0.40"
DEFAULT_STEPS = "30"
DEFAULT_NUM_VERSIONS = "1"
DEFAULT_FPS = "16"
DEFAULT_WIDTH = "1280"
DEFAULT_HEIGHT = "720"

LOG_DIR = os.path.join(STAGING_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


def configure_console_encoding():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def safe_text(text):
    if text is None:
        return ""
    t = text.encode("ascii", errors="replace").decode("ascii")
    if len(t) > 4000:
        return t[:4000] + " ... [truncated]"
    return t


def run_cmd(cmd, timeout=600, check=True):
    env = os.environ.copy()
    env["JL_API_KEY"] = API_KEY
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        cmd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=env,
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc


def ensure_files():
    if not os.path.exists(PLAN_FILE):
        raise FileNotFoundError(f"Missing segment plan: {PLAN_FILE}")
    if not os.path.exists(REFINE_SCRIPT_PATH):
        raise FileNotFoundError(f"Missing staging refine script: {REFINE_SCRIPT_PATH}")

    lines = [
        "torch>=2.0.0",
        "torchvision",
        "diffusers>=0.33.0,<0.38.0",
        "transformers==4.49.0",
        "accelerate",
        "imageio[ffmpeg]",
        "sentencepiece",
        "protobuf>=4.25.3",
        "tiktoken",
    ]
    with open(REQUIREMENTS_FILE, "w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def jl(*args, timeout=600, check=True):
    cmd = [sys.executable, os.path.join(ROOT, "manage_jl.py"), *args]
    return run_cmd(cmd, timeout=timeout, check=check)


def list_instances_json():
    out = jl("list", "--json", timeout=120).stdout.strip()
    return json.loads(out or "[]")


def cleanup_stale_instances():
    instances = list_instances_json()
    targets = [
        m
        for m in instances
        if m.get("name", "").startswith("fix-") or m.get("name") == "jl-run"
    ]
    if not targets:
        return 0
    for m in targets:
        mid = str(m["machine_id"])
        jl("destroy", "-y", mid, timeout=120, check=False)
    return len(targets)


def read_plan():
    with open(PLAN_FILE, "r", encoding="utf-8") as f:
        plan = json.load(f)
    return [s for s in plan if s.get("type") == "BAD"]


def create_instance(name):
    last_error = None
    for _ in range(3):
        args = [
            "create",
            "--gpu",
            GPU_TYPE,
            "--region",
            GPU_REGION,
            "--storage",
            str(STORAGE_GB),
            "--name",
            name,
            "--yes",
            "--json",
        ]
        try:
            out = jl(*args, timeout=180).stdout
            data = json.loads(out)
            return int(data["machine_id"])
        except Exception as e:
            last_error = str(e)
            time.sleep(4)

    raise RuntimeError(last_error or "Could not create instance in IN2")


def upload_file(machine_id, local_path, remote_path):
    jl("upload", str(machine_id), local_path, remote_path, timeout=1200)


def exec_remote(machine_id, command):
    jl("exec", str(machine_id), "--", "bash", "-lc", command, timeout=5400)


def download_file(machine_id, remote_path, local_path):
    jl("download", str(machine_id), remote_path, local_path, timeout=1800)


def destroy_instance(machine_id):
    jl("destroy", "-y", str(machine_id), timeout=120, check=False)


def segment_paths(label):
    stage_input = os.path.join(
        STAGING_ROOT, "ALL_VIDEOS", "BAD_SEGMENTS", f"{label}.mp4"
    )
    stage_output = os.path.join(
        STAGING_ROOT, "ALL_VIDEOS", "BAD_SEGMENTS", f"{label}_REFINED.mp4"
    )
    final_output = os.path.join(
        ROOT, "ALL_VIDEOS", "BAD_SEGMENTS", f"{label}_REFINED.mp4"
    )
    return stage_input, stage_output, final_output


def segment_log_path(label):
    return os.path.join(LOG_DIR, f"{label}.log")


def process_segment(segment):
    label = segment["label"]
    prompt = segment["v2v_prompt"]
    instance_name = f"fix-{label.replace('_', '-')}"[:63]
    stage_input, stage_output, final_output = segment_paths(label)
    log_file = segment_log_path(label)

    if not os.path.exists(stage_input):
        return {"label": label, "ok": False, "error": f"Missing input: {stage_input}"}

    attempt_errors = []
    for attempt in range(1, MAX_SEGMENT_ATTEMPTS + 1):
        machine_id = None
        try:
            machine_id = create_instance(instance_name)

            with open(log_file, "a", encoding="utf-8") as lf:
                lf.write(f"attempt={attempt} instance_id={machine_id}\n")

            upload_file(machine_id, REFINE_SCRIPT_PATH, "/home/refine_drone_video.py")
            upload_file(machine_id, REQUIREMENTS_FILE, "/home/requirements_refine.txt")
            upload_file(machine_id, stage_input, f"/home/{label}.mp4")

            setup_cmd = "python -m pip install -r /home/requirements_refine.txt"
            run_cmdline = [
                "python",
                "/home/refine_drone_video.py",
                "--input_video",
                f"/home/{label}.mp4",
                "--output_video",
                f"/home/{label}_REFINED.mp4",
                "--prompt",
                prompt,
                "--strength",
                DEFAULT_STRENGTH,
                "--steps",
                DEFAULT_STEPS,
                "--num_versions",
                DEFAULT_NUM_VERSIONS,
                "--fps",
                DEFAULT_FPS,
                "--width",
                DEFAULT_WIDTH,
                "--height",
                DEFAULT_HEIGHT,
            ]
            remote = setup_cmd + " && " + " ".join(shlex.quote(x) for x in run_cmdline)
            exec_remote(machine_id, remote)

            download_file(machine_id, f"/home/{label}_REFINED.mp4", stage_output)
            if not os.path.exists(stage_output) or os.path.getsize(stage_output) == 0:
                raise RuntimeError(f"Downloaded output missing/empty: {stage_output}")

            os.makedirs(os.path.dirname(final_output), exist_ok=True)
            with open(stage_output, "rb") as src, open(final_output, "wb") as dst:
                dst.write(src.read())

            return {
                "label": label,
                "ok": True,
                "machine_id": machine_id,
                "output": stage_output,
                "attempt": attempt,
            }
        except Exception as e:
            err = safe_text(str(e))
            attempt_errors.append(f"attempt {attempt}: {err}")
            with open(log_file, "a", encoding="utf-8") as lf:
                lf.write(f"attempt={attempt} error={err}\n")
        finally:
            if machine_id is not None:
                destroy_instance(machine_id)

    return {
        "label": label,
        "ok": False,
        "error": " | ".join(attempt_errors),
    }


def write_plan_status(results):
    if not os.path.exists(PLAN_FILE):
        return
    with open(PLAN_FILE, "r", encoding="utf-8") as f:
        plan = json.load(f)

    by_label = {r["label"]: r for r in results}
    for seg in plan:
        label = seg.get("label")
        if label in by_label and seg.get("type") == "BAD":
            seg["status"] = "refined" if by_label[label]["ok"] else "error"

    with open(PLAN_FILE, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    if os.path.exists(LOCAL_PLAN_MIRROR):
        with open(LOCAL_PLAN_MIRROR, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Robust BAD-segment refiner")
    parser.add_argument(
        "--labels",
        nargs="*",
        default=None,
        help="Optional list of BAD segment labels to run",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=MAX_WORKERS,
        help="Parallel worker count",
    )
    args = parser.parse_args()

    try:
        ensure_files()
    except Exception as e:
        print(f"ERROR: {e}")
        return

    cleaned = cleanup_stale_instances()
    if cleaned:
        print(f"Cleaned {cleaned} stale instances before launch.")

    bad_segments = read_plan()
    if args.labels:
        wanted = set(args.labels)
        bad_segments = [s for s in bad_segments if s["label"] in wanted]

    if not bad_segments:
        print("No BAD segments found in plan.")
        return

    print("-" * 60)
    print(f"STARTING robust refinement: {len(bad_segments)} BAD segments")
    print(
        f"GPU: {GPU_TYPE} | Region: {GPU_REGION} | Steps: {DEFAULT_STEPS} | Versions: {DEFAULT_NUM_VERSIONS}"
    )
    if args.labels:
        print(f"Labels: {', '.join(args.labels)}")
    print("-" * 60)

    results = []
    worker_count = max(1, min(args.max_workers, len(bad_segments)))
    with ThreadPoolExecutor(max_workers=worker_count) as ex:
        fut_to_label = {}
        for seg in bad_segments:
            fut = ex.submit(process_segment, seg)
            fut_to_label[fut] = seg["label"]
            time.sleep(STAGGER_SECONDS)

        for fut in as_completed(fut_to_label):
            res = fut.result()
            results.append(res)
            if res["ok"]:
                print(f"OK   {res['label']}")
            else:
                print(
                    f"FAIL {res['label']} :: {safe_text(res.get('error', 'unknown error'))}"
                )

    write_plan_status(results)

    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count
    print("-" * 60)
    print(f"DONE: success={ok_count}, failed={fail_count}")
    print(f"Logs: {LOG_DIR}")
    print("-" * 60)


if __name__ == "__main__":
    configure_console_encoding()
    main()
