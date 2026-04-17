"""Wan 2.2 — Text-to-Video Generation (14B, H100 optimized)"""

import argparse
import torch
import os
import time


def main():
    parser = argparse.ArgumentParser(description="Wan 2.2 14B Video Generation")
    parser.add_argument(
        "--prompt", type=str, required=True, help="Text prompt for video generation"
    )
    parser.add_argument(
        "--output", type=str, default="output.mp4", help="Output video filename"
    )
    parser.add_argument(
        "--num-frames",
        type=int,
        default=81,
        help="Number of frames (default: 81 = ~5s at 16fps)",
    )
    parser.add_argument(
        "--height", type=int, default=720, help="Video height (default: 720)"
    )
    parser.add_argument(
        "--width", type=int, default=1280, help="Video width (default: 1280)"
    )
    parser.add_argument(
        "--steps", type=int, default=30, help="Inference steps (default: 30)"
    )
    parser.add_argument(
        "--guidance", type=float, default=5.0, help="Guidance scale (default: 5.0)"
    )
    args = parser.parse_args()

    start = time.time()

    print("🎬 Wan 2.2 14B — Loading pipeline...")
    print(f"   GPU: {torch.cuda.get_device_name(0)}")
    print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    from diffusers import AutoencoderKLWan, WanPipeline
    from diffusers.utils import export_to_video

    # Load VAE
    vae = AutoencoderKLWan.from_pretrained(
        "Wan-AI/Wan2.2-T2V-A14B-Diffusers",
        subfolder="vae",
        torch_dtype=torch.float32,
    )

    # Load full pipeline with bfloat16 for speed on H100
    pipe = WanPipeline.from_pretrained(
        "Wan-AI/Wan2.2-T2V-A14B-Diffusers",
        vae=vae,
        torch_dtype=torch.bfloat16,
    )
    pipe.to("cuda")

    # Enable memory optimizations
    pipe.enable_model_cpu_offload()

    load_time = time.time() - start
    print(f"   Pipeline loaded in {load_time:.1f}s")

    print(f"\n🎬 Generating video...")
    print(f"   Prompt: {args.prompt}")
    print(f"   Resolution: {args.width}x{args.height}")
    print(
        f"   Frames: {args.num_frames} | Steps: {args.steps} | Guidance: {args.guidance}"
    )

    gen_start = time.time()

    output = pipe(
        prompt=args.prompt,
        num_frames=args.num_frames,
        height=args.height,
        width=args.width,
        num_inference_steps=args.steps,
        guidance_scale=args.guidance,
        generator=torch.Generator("cpu").manual_seed(42),
    )

    gen_time = time.time() - gen_start
    print(f"   Generation completed in {gen_time:.1f}s")

    # Save video
    out_path = os.path.abspath(args.output)
    export_to_video(output.frames[0], out_path, fps=16)

    total = time.time() - start
    print(f"\n✅ Done in {total:.1f}s total!")
    print(f"   Video: {out_path}")


if __name__ == "__main__":
    main()
