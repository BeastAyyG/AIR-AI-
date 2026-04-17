import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(r"C:/happy horse")
INPUT_GLOB = "WhatsApp Image 2026-04-12 at 9.24.*.jpeg"
PREP_DIR = ROOT / "_drone_prep"
VIDEO_ONLY = ROOT / "drone_consistent_v2_video.mp4"
FINAL_OUTPUT = ROOT / "drone_consistent_v2_with_audio.mp4"

FPS = 30
CLIP_SEC = 4.0
XFADE_SEC = 1.0
OUT_W = 1280
OUT_H = 720


def read_img(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0


def write_img(arr: np.ndarray, path: Path) -> None:
    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    Image.fromarray(arr).save(path)


def match_color(src: np.ndarray, ref: np.ndarray) -> np.ndarray:
    eps = 1e-6
    out = src.copy()
    for c in range(3):
        s = src[:, :, c]
        r = ref[:, :, c]
        s_mean, s_std = s.mean(), s.std() + eps
        r_mean, r_std = r.mean(), r.std() + eps
        out[:, :, c] = ((s - s_mean) * (r_std / s_std)) + r_mean
    return np.clip(out, 0, 1)


def build_video_filter(count: int) -> str:
    parts = []
    frames_per_clip = int(CLIP_SEC * FPS)

    for idx in range(count):
        x_drift = "7*sin(on/31)" if idx % 2 == 0 else "-7*sin(on/31)"
        y_drift = "5*cos(on/37)" if idx % 2 == 0 else "-5*cos(on/37)"
        zoom_expr = "if(lte(on,1),1.0,min(zoom+0.00055,1.09))"
        parts.append(
            f"[{idx}:v]scale=1600:900,"
            f"zoompan=z='{zoom_expr}':d={frames_per_clip}:"
            f"x='(iw-iw/zoom)/2+{x_drift}':"
            f"y='(ih-ih/zoom)/2+{y_drift}':"
            f"s={OUT_W}x{OUT_H}:fps={FPS},"
            "eq=contrast=1.03:saturation=1.05:brightness=0.01,"
            "unsharp=5:5:0.35:5:5:0.0,"
            f"format=yuv420p[v{idx}]"
        )

    offset = CLIP_SEC - XFADE_SEC
    parts.append(
        f"[v0][v1]xfade=transition=fade:duration={XFADE_SEC}:offset={offset}[x1]"
    )
    for idx in range(2, count):
        offset += CLIP_SEC - XFADE_SEC
        parts.append(
            f"[x{idx - 1}][v{idx}]xfade=transition=fade:duration={XFADE_SEC}:offset={offset}[x{idx}]"
        )

    return ";".join(parts)


def main() -> None:
    source_paths = sorted(ROOT.glob(INPUT_GLOB))
    if len(source_paths) < 2:
        raise RuntimeError("Need at least 2 JPEG photos to animate.")

    if PREP_DIR.exists():
        shutil.rmtree(PREP_DIR)
    PREP_DIR.mkdir(parents=True, exist_ok=True)

    reference = read_img(source_paths[0])
    prepared = []
    for idx, src in enumerate(source_paths):
        corrected = match_color(read_img(src), reference)
        out_path = PREP_DIR / f"img_{idx:03d}.png"
        write_img(corrected, out_path)
        prepared.append(out_path)

    video_cmd = ["ffmpeg", "-y"]
    for path in prepared:
        video_cmd += ["-loop", "1", "-t", f"{CLIP_SEC}", "-i", str(path)]
    video_cmd += [
        "-filter_complex",
        build_video_filter(len(prepared)),
        "-map",
        f"[x{len(prepared) - 1}]",
        "-c:v",
        "h264_nvenc",
        "-preset",
        "p6",
        "-cq:v",
        "18",
        "-pix_fmt",
        "yuv420p",
        str(VIDEO_ONLY),
    ]
    subprocess.run(video_cmd, check=True)

    audio_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(VIDEO_ONLY),
        "-f",
        "lavfi",
        "-i",
        "anoisesrc=color=pink:amplitude=0.025:sample_rate=48000",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=95:sample_rate=48000",
        "-filter_complex",
        "[1:a]lowpass=f=1300,highpass=f=120,volume=0.16[a0];"
        "[2:a]lowpass=f=220,volume=0.09[a1];"
        "[a0][a1]amix=inputs=2:weights='1 0.8',"
        "afade=t=in:st=0:d=1.5,afade=t=out:st=20:d=2[aout]",
        "-map",
        "0:v:0",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(FINAL_OUTPUT),
    ]
    subprocess.run(audio_cmd, check=True)

    print(f"Created: {FINAL_OUTPUT}")


if __name__ == "__main__":
    main()
