import argparse
import inspect
import os
import torch
import warnings

warnings.filterwarnings(
    "ignore", message=".*Torch was not compiled with flash attention.*"
)
from diffusers import CogVideoXVideoToVideoPipeline
from diffusers.utils import export_to_video, load_video
from transformers import T5Tokenizer


def main():
    parser = argparse.ArgumentParser(
        description="Refine an existing generated drone video to fix morphing/details."
    )
    parser.add_argument(
        "--input_video",
        type=str,
        default="drone_video_ultra_fidelity.mp4",
        help="Path to the mp4 you want to refine",
    )
    parser.add_argument(
        "--output_video",
        type=str,
        default="drone_video_refined.mp4",
        help="Path to save the refined mp4",
    )
    default_drone_prompt = (
        "Autonomous Heavy-Lift Medical Evacuation Octocopter (eVTOL). Flat octocopter architecture with 8 rotors "
        "around a rectangular carbon-fiber core chassis. Exposed rigid cylindrical carbon fiber sub-frame with red and black structural nodes. "
        "8 heavy-lift brushless outrunner motors on extended straight arms, large two-blade carbon fiber propellers. "
        "Dark-tinted semi-transparent aerodynamic barrel-vault canopy covering a medical stretcher bed. "
        "Fixed 4-point tubular landing gear skids with neon-green joint brackets. "
        "Bright orange/red LED perimeter beacons, interior flashing red and blue emergency strobes under the canopy, "
        "downward white LED landing illumination. Ultra-realistic, cinematic lighting, 8k resolution, exact geometric proportions perfectly maintained."
    )

    parser.add_argument(
        "--prompt",
        type=str,
        default=default_drone_prompt,
        help="Prompt to guide the refinement",
    )
    parser.add_argument(
        "--strength",
        type=float,
        default=0.4,
        help="Amount of change to apply. 0.0 is original video, 1.0 is completely new generation. Keep low (0.3-0.5) to fix morphing without losing original motion.",
    )
    parser.add_argument(
        "--guidance", type=float, default=6.0, help="Classifier free guidance scale"
    )
    parser.add_argument(
        "--steps", type=int, default=30, help="Number of inference steps"
    )
    parser.add_argument(
        "--num_versions",
        type=int,
        default=1,
        help="How many variants to generate per segment",
    )
    parser.add_argument("--fps", type=int, default=16, help="Output FPS")
    parser.add_argument("--width", type=int, default=1280, help="Output width")
    parser.add_argument("--height", type=int, default=720, help="Output height")
    args = parser.parse_args()

    if not os.path.exists(args.input_video):
        raise FileNotFoundError(f"Could not find input video: {args.input_video}")

    print(f"Loading CogVideoX Video-to-Video Pipeline...")
    tokenizer = T5Tokenizer.from_pretrained(
        "THUDM/CogVideoX-5b", subfolder="tokenizer", use_fast=False
    )
    # Using the base CogVideoX-5b model as it reliably supports the V2V pipeline.
    pipe = CogVideoXVideoToVideoPipeline.from_pretrained(
        "THUDM/CogVideoX-5b", tokenizer=tokenizer, torch_dtype=torch.bfloat16
    ).to("cuda")

    # Memory optimization
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()

    print(f"Loading input video: {args.input_video}")
    video_frames = load_video(args.input_video)

    num_versions = max(1, args.num_versions)
    print(
        f"Refining video with {num_versions} different versions (varying seeds and strength) for prompt: '{args.prompt}'"
    )

    call_params = inspect.signature(pipe.__call__).parameters
    supports_num_frames = "num_frames" in call_params
    supports_width = "width" in call_params
    supports_height = "height" in call_params

    for i in range(num_versions):
        current_seed = 42 + (i * 100)
        current_strength = args.strength + (i * 0.05)  # Slight variation in strength
        if num_versions == 1:
            version_name = args.output_video
        else:
            version_name = args.output_video.replace(
                ".mp4", f"_v{i + 1}_str_{current_strength:.2f}.mp4"
            )

        print(
            f"\n--- Generating Version {i + 1}/{num_versions} (Seed: {current_seed}, Strength: {current_strength:.2f}) ---"
        )

        call_kwargs = dict(
            prompt=args.prompt,
            video=video_frames,
            num_inference_steps=args.steps,
            use_dynamic_cfg=True,
            guidance_scale=args.guidance,
            strength=current_strength,
            generator=torch.Generator("cpu").manual_seed(current_seed),
        )
        if supports_num_frames:
            call_kwargs["num_frames"] = len(video_frames)
        if supports_width:
            call_kwargs["width"] = args.width
        if supports_height:
            call_kwargs["height"] = args.height

        out_frames = pipe(**call_kwargs).frames[0]

        print(f"Saving refined video to: {version_name}")
        export_to_video(out_frames, version_name, fps=args.fps)

    print(f"Completed {num_versions} version(s).")


if __name__ == "__main__":
    main()
