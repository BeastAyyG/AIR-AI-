import torch, os, sys, gc
from diffusers import CogVideoXPipeline, CogVideoXImageToVideoPipeline
from diffusers.utils import export_to_video, load_image

base_style = "Kurzgesagt 2D flat animation, deep navy #1a1a2e background, thick black outlines, bold flat colors, chunky rounded cartoon style, no photorealism, no gradients, 16:9"

shots = {
    1: ("t2v", f"{base_style}. cartoon hospital control room, large glowing red screen flashing CRITICAL AIR UNIT DISPATCHED, chunky rounded operator characters at glowing monitors, amber and teal screen glow"),
    2: ("i2v", f"{base_style}. SW-1 Alpha cartoon drone on rooftop launchpad, deep navy sky, black grid-pattern body, 12 propellers in 6 arm pairs, green and red LED dots on motors, orange launchpad glow underneath, city skyline silhouette"),
    3: ("t2v", f"{base_style}. two cartoon paramedics in orange vests sliding white medical pod into drone underside on hospital rooftop, lock clicking with green checkmark bubble, status light turning green"),
    4: ("i2v", f"{base_style}. SW-1 Alpha drone lifting off rooftop helipad, amber downwash rings expanding outward, two cartoon paramedics shielding faces leaning back, upward speed lines, golden city skyline below"),
    5: ("i2v", f"{base_style}. chase shot of SW-1 Alpha drone flying above gridlocked cartoon highway at night, bold red and amber car light trail streaks below, chunky skyscrapers with warm yellow windows"),
    6: ("t2v", f"{base_style}. infographic animation, glowing teal heartbeat line pulsing, amber text showing 97 percent SpO2 and 78 BPM, GPS route map with orange dotted trail moving to red cross hospital icon"),
    7: ("i2v", f"{base_style}. bird eye view of SW-1 Alpha drone descending onto glowing hospital rooftop pad with large H symbol, orange guide lights, three cartoon medical staff rushing forward"),
    8: ("t2v", f"{base_style}. three cartoon doctors opening drone hatch pulling out white medical pod, warm golden hospital door light, urgent motion lines on characters, red cross on equipment"),
    9: ("t2v", f"{base_style}. end card, white bold text SW-1 ALPHA, amber text When the sky is the fastest road, flat cartoon drone silhouette icon, single blinking green LED dot, smooth fade-in"),
}

shot_id = int(sys.argv[1])
shot_type, prompt = shots[shot_id]
out_file = f"/home/out_shot_{shot_id}.mp4"

print(f"Generating shot {shot_id} ({shot_type})...", flush=True)

if shot_type == "t2v":
    pipe = CogVideoXPipeline.from_pretrained("THUDM/CogVideoX-5b", torch_dtype=torch.bfloat16).to("cuda")
else:
    pipe = CogVideoXImageToVideoPipeline.from_pretrained("THUDM/CogVideoX-5b-I2V", torch_dtype=torch.bfloat16).to("cuda")

pipe.enable_model_cpu_offload()
pipe.vae.enable_tiling()

kwargs = dict(prompt=prompt, num_inference_steps=50, num_frames=49, guidance_scale=6, generator=torch.Generator("cpu").manual_seed(42))
if shot_type == "i2v":
    kwargs["image"] = load_image("/home/reference_drone.png")

frames = pipe(**kwargs).frames[0]
export_to_video(frames, out_file, fps=8)
print(f"Done: {out_file}", flush=True)
