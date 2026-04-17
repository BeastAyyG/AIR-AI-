import torch
import os
from diffusers import CogVideoXPipeline, CogVideoXImageToVideoPipeline
from diffusers.utils import export_to_video, load_image
from moviepy import VideoFileClip, concatenate_videoclips

base_style = "Kurzgesagt 2D flat animation, deep navy #1a1a2e background, thick black outlines, bold flat colors, chunky rounded cartoon style, no photorealism, no gradients, 16:9"

shots = [
    {
        "type": "t2v",
        "prompt": f"{base_style}. cartoon hospital control room, large glowing red screen flashing 'CRITICAL — AIR UNIT DISPATCHED', chunky rounded operator characters at glowing monitors, amber and teal screen glow"
    },
    {
        "type": "i2v",
        "prompt": f"{base_style}. SW-1 Alpha cartoon drone on rooftop launchpad, deep navy sky, black grid-pattern body, 12 propellers in 6 arm pairs, green and red LED dots on motors, propellers spinning with Kurzgesagt motion arc lines, orange launchpad glow underneath, city skyline silhouette behind"
    },
    {
        "type": "t2v",
        "prompt": f"{base_style}. two cartoon paramedics in orange vests sliding white medical pod into drone underside on hospital rooftop, red and blue emergency glow beams, lock clicking with green checkmark bubble, status light turning green, chunky rounded characters, deep navy night"
    },
    {
        "type": "i2v",
        "prompt": f"{base_style}. SW-1 Alpha drone lifting off rooftop helipad, amber downwash rings expanding outward, two cartoon paramedics shielding faces leaning back, green LED blinks on drone arms, upward speed lines, golden city skyline below, camera pulling back dramatically"
    },
    {
        "type": "i2v",
        "prompt": f"{base_style}. chase shot of SW-1 Alpha drone flying above gridlocked cartoon highway at night, bold red and amber car light trail streaks below, chunky skyscrapers with warm yellow windows on both sides, speed lines on edges, green LED dots on drone arms"
    },
    {
        "type": "t2v",
        "prompt": f"{base_style}. infographic animation, glowing teal heartbeat line pulsing, amber text showing 97% SpO2 and 78 BPM, GPS route map with orange dotted trail moving to red cross hospital icon, speed and altitude readout, countdown timer, bold rounded UI panels"
    },
    {
        "type": "i2v",
        "prompt": f"{base_style}. bird's eye view of SW-1 Alpha drone descending onto glowing hospital rooftop pad with large H symbol, orange guide lights, three cartoon medical staff rushing forward arms out, propeller reverse motion arcs, amber pad glow under drone"
    },
    {
        "type": "t2v",
        "prompt": f"{base_style}. three cartoon doctors opening drone hatch pulling out white medical pod, one attaching glowing monitor showing heartbeat, warm golden hospital door light behind them, urgent motion lines on characters, red cross on equipment"
    },
    {
        "type": "t2v",
        "prompt": f"{base_style}. end card, white bold text fading in 'SW-1 ALPHA', amber text below 'When the sky is the fastest road', flat cartoon drone silhouette icon above in white thick lines, single blinking green LED dot, smooth fade-in, minimal clean design"
    }
]

def main():
    print("🚀 Initializing CogVideoX Pipelines...")
    
    # Load Image-to-Video Pipeline
    pipe_i2v = CogVideoXImageToVideoPipeline.from_pretrained("THUDM/CogVideoX-5b-I2V", torch_dtype=torch.bfloat16).to("cuda")
    pipe_i2v.enable_model_cpu_offload()
    pipe_i2v.vae.enable_tiling()
    
    # Load Text-to-Video Pipeline
    pipe_t2v = CogVideoXPipeline.from_pretrained("THUDM/CogVideoX-5b", torch_dtype=torch.bfloat16).to("cuda")
    pipe_t2v.enable_model_cpu_offload()
    pipe_t2v.vae.enable_tiling()

    # Determine reference image
    ref_image_path = "reference_drone.png"
    if os.path.exists(ref_image_path):
        ref_image = load_image(ref_image_path)
    else:
        print(f"⚠️ Warning: '{ref_image_path}' not found. I2V shots will fallback to T2V.")
        ref_image = None

    generated_clips = []

    for i, shot in enumerate(shots, 1):
        filename = f"out_shot_{i}.mp4"
        print(f"\n🎬 Generating SHOT {i}/9: {shot['prompt'][:60]}...")
        
        # Free up VRAM dynamically just in case
        torch.cuda.empty_cache()
        
        if shot["type"] == "i2v" and ref_image:
            video_frames = pipe_i2v(
                prompt=shot["prompt"],
                image=ref_image,
                num_inference_steps=50,
                num_frames=49,
                guidance_scale=6,
                generator=torch.Generator("cpu").manual_seed(42),
            ).frames[0]
        else:
            video_frames = pipe_t2v(
                prompt=shot["prompt"],
                num_inference_steps=50,
                num_frames=49,
                guidance_scale=6,
                generator=torch.Generator("cpu").manual_seed(42),
            ).frames[0]

        export_to_video(video_frames, filename, fps=8)
        generated_clips.append(filename)

    print("\n🎞️ Stitching all 9 shots into final masterpiece...")
    clips = [VideoFileClip(c) for c in generated_clips]
    final_video = concatenate_videoclips(clips)
    final_video.write_videofile("FINAL_SW1_MOVIE.mp4", codec="libx264")
    
    print("✅ All done! Movie saved as FINAL_SW1_MOVIE.mp4")

if __name__ == "__main__":
    main()
