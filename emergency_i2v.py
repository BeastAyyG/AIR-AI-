import argparse
import torch
from diffusers import CogVideoXImageToVideoPipeline
from diffusers.utils import export_to_video, load_image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", default="context_emergency.mp4")
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()

    pipe = CogVideoXImageToVideoPipeline.from_pretrained(
        "THUDM/CogVideoX-5b-I2V",
        torch_dtype=torch.bfloat16,
    ).to("cuda")
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()

    image = load_image(args.image)
    frames = pipe(
        prompt=args.prompt,
        image=image,
        num_inference_steps=50,
        num_frames=49,
        guidance_scale=6,
        generator=torch.Generator("cpu").manual_seed(42),
    ).frames[0]
    export_to_video(frames, args.output, fps=8)
    print(f"DONE: {args.output}", flush=True)


if __name__ == "__main__":
    main()
