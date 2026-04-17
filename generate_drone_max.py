import argparse
import glob
import os

import torch
from diffusers import CogVideoXImageToVideoPipeline
from diffusers.utils import export_to_video, load_image
from moviepy import VideoFileClip, concatenate_videoclips


def find_reference_images(max_refs: int):
    preferred = [
        "reference_drone.png",
        "ref1.jpeg",
        "ref2.jpeg",
        "ref3.jpeg",
        "ref4.jpeg",
        "ref5.jpeg",
        "ref6.jpeg",
    ]
    found = [p for p in preferred if os.path.exists(p)]

    if len(found) < max_refs:
        for pattern in ("WhatsApp Image *.jpeg", "*.png", "*.jpg", "*.jpeg"):
            for p in glob.glob(pattern):
                if p not in found and os.path.isfile(p):
                    found.append(p)

    return found[:max_refs]


def build_variants():
    return [
        {
            "name": "drone_video_context_best_fidelity.mp4",
            "steps": 30,
            "frames": 41,
            "guidance": 6.0,
            "seed": 100,
            "prompt": (
                "Cinematic emergency response drone shot. Preserve the exact drone shape, body proportions, "
                "landing gear, and colors from the reference image. Realistic look, sharp detail, accurate geometry, "
                "controlled smooth camera movement, city rooftop and skyline context, no cartoon style"
            ),
        },
        {
            "name": "drone_video_context_best_motion.mp4",
            "steps": 28,
            "frames": 49,
            "guidance": 5.0,
            "seed": 200,
            "prompt": (
                "High-energy cinematic drone sequence based on the reference image. Fast aerial tracking, "
                "banking turns, rise and descend passes, dramatic emergency mood, night city lights, realistic materials, "
                "maintain recognizable drone identity from the reference"
            ),
        },
        {
            "name": "drone_video_context_best_balanced.mp4",
            "steps": 32,
            "frames": 45,
            "guidance": 5.5,
            "seed": 300,
            "prompt": (
                "Premium cinematic drone hero video from reference photo. Keep the same drone design and colors, "
                "combine smooth dynamic motion with visual fidelity, realistic lighting, emergency-response story feel, "
                "high detail and stable composition"
            ),
        },
    ]


def render_variant(pipe, refs, variant):
    tmp_clips = []
    for i, ref in enumerate(refs, start=1):
        print(f"[{variant['name']}] clip {i}/{len(refs)} from {ref}", flush=True)
        image = load_image(ref)
        frames = pipe(
            prompt=variant["prompt"],
            image=image,
            num_inference_steps=variant["steps"],
            num_frames=variant["frames"],
            guidance_scale=variant["guidance"],
            generator=torch.Generator("cpu").manual_seed(variant["seed"] + i),
        ).frames[0]
        clip_name = f"tmp_{os.path.splitext(variant['name'])[0]}_{i}.mp4"
        export_to_video(frames, clip_name, fps=8)
        tmp_clips.append(clip_name)

    if len(tmp_clips) == 1:
        os.replace(tmp_clips[0], variant["name"])
        return

    clips = [VideoFileClip(c) for c in tmp_clips]
    final = concatenate_videoclips(clips)
    final.write_videofile(variant["name"], codec="libx264")


def main():
    parser = argparse.ArgumentParser(
        description="Generate strongest context-photo drone variants"
    )
    parser.add_argument("--max-refs", type=int, default=4)
    args = parser.parse_args()

    refs = find_reference_images(args.max_refs)
    if not refs:
        raise RuntimeError("No reference images available")

    print("Using refs:")
    for r in refs:
        print(f" - {r}")

    print("Loading CogVideoX I2V once for all variants...")
    pipe = CogVideoXImageToVideoPipeline.from_pretrained(
        "THUDM/CogVideoX-5b-I2V", torch_dtype=torch.bfloat16
    ).to("cuda")
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()

    for variant in build_variants():
        print(f"\nRendering {variant['name']} ...", flush=True)
        render_variant(pipe, refs, variant)
        print(f"Done {variant['name']}", flush=True)

    print("All variants complete.")


if __name__ == "__main__":
    main()
