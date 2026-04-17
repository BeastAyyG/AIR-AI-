import argparse
import glob
import os

import torch
from diffusers import CogVideoXImageToVideoPipeline
from diffusers.utils import export_to_video, load_image
from moviepy import VideoFileClip, concatenate_videoclips


def find_reference_images(max_refs: int):
    patterns = [
        "reference_drone.png",
        "WhatsApp Image *.jpeg",
        "WhatsApp Image *.jpg",
        "*.png",
        "*.jpeg",
        "*.jpg",
    ]

    candidates = []
    for pattern in patterns:
        for path in glob.glob(pattern):
            name = os.path.basename(path).lower()
            if name.endswith((".png", ".jpg", ".jpeg")) and "dashboard" not in name:
                candidates.append(path)

    # De-duplicate while preserving order
    seen = set()
    ordered = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered.append(c)

    return ordered[:max_refs]


def main():
    parser = argparse.ArgumentParser(
        description="Generate drone video using provided context photos"
    )
    parser.add_argument("--output", type=str, default="drone_video_context.mp4")
    parser.add_argument("--max-refs", type=int, default=3)
    parser.add_argument("--steps", type=int, default=28)
    parser.add_argument("--num-frames", type=int, default=33)
    args = parser.parse_args()

    refs = find_reference_images(args.max_refs)
    if not refs:
        raise RuntimeError("No reference images found in working directory")

    print("Using reference photos:")
    for r in refs:
        print(f" - {r}")

    print("Loading CogVideoX I2V pipeline...")
    pipe = CogVideoXImageToVideoPipeline.from_pretrained(
        "THUDM/CogVideoX-5b-I2V", torch_dtype=torch.bfloat16
    ).to("cuda")
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()

    prompt = (
        "Cinematic emergency response drone video, preserve the exact drone shape and colors from the reference photo, "
        "fast aerial motion, city environment, dramatic but realistic lighting, smooth camera movement, high detail"
    )

    clip_paths = []
    for i, ref_path in enumerate(refs, start=1):
        print(f"Generating clip {i}/{len(refs)} from {ref_path}...")
        image = load_image(ref_path)
        frames = pipe(
            prompt=prompt,
            image=image,
            num_inference_steps=args.steps,
            num_frames=args.num_frames,
            guidance_scale=5.0,
            generator=torch.Generator("cpu").manual_seed(42 + i),
        ).frames[0]

        out_clip = f"context_clip_{i}.mp4"
        export_to_video(frames, out_clip, fps=8)
        clip_paths.append(out_clip)

    if len(clip_paths) == 1:
        os.replace(clip_paths[0], args.output)
        print(f"Done: {os.path.abspath(args.output)}")
        return

    print("Stitching clips...")
    clips = [VideoFileClip(p) for p in clip_paths]
    final = concatenate_videoclips(clips)
    final.write_videofile(args.output, codec="libx264")
    print(f"Done: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
