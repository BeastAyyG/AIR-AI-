import argparse
import torch
import os
from diffusers import CogVideoXPipeline
from diffusers.utils import export_to_video

def main():
    parser = argparse.ArgumentParser(description="Text-to-Video Generation with JarvisLabs")
    parser.add_argument("--prompt", type=str, required=True, help="Description of the video you want to generate")
    parser.add_argument("--output", type=str, default="output.mp4", help="Output file path (e.g., output.mp4)")
    args = parser.parse_args()

    print("🚀 Initializing Text-to-Video Pipeline (CogVideoX-5b)...")
    # Using bfloat16 to optimize memory and maintain quality
    pipe = CogVideoXPipeline.from_pretrained(
        "THUDM/CogVideoX-5b", 
        torch_dtype=torch.bfloat16
    ).to("cuda")
    
    # Memory optimizations essential for high-end GPUs like A6000 or L4
    pipe.enable_model_cpu_offload() 
    pipe.vae.enable_tiling()

    print(f"\n🎬 Generating video for prompt: '{args.prompt}'")
    print("⏳ This will take a few minutes. Grab a coffee...")
    
    # Generate the frames
    video_frames = pipe(
        prompt=args.prompt,
        num_inference_steps=50,
        num_frames=49, # 49 frames is default for CogVideoX
        guidance_scale=6,
        generator=torch.Generator("cpu").manual_seed(42),
    ).frames[0]

    # Resolve absolute path to ensure we know exactly where it is saved
    out_path = os.path.abspath(args.output)
    
    print(f"\n💾 Exporting video to {out_path}...")
    export_to_video(video_frames, out_path, fps=8)
    print(f"✅ Video generation complete! Your video is ready to be downloaded.")

if __name__ == "__main__":
    main()
