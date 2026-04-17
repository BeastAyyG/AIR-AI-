import os

import torch
from diffusers import CogVideoXImageToVideoPipeline
from diffusers.utils import export_to_video, load_image
from moviepy import VideoFileClip, concatenate_videoclips


def main():
    refs = [
        p
        for p in ["reference_drone.png", "ref1.jpeg", "ref2.jpeg"]
        if os.path.exists(p)
    ]
    if not refs:
        raise RuntimeError("No reference images found")

    prompt = (
        "Photorealistic autonomous heavy-lift medical evacuation octocopter eVTOL, flat octocopter architecture, "
        "8 rotors in one horizontal plane around a thick rectangular carbon-fiber core chassis, rigid cylindrical carbon-fiber tube grid sub-frame, "
        "block structural nodes, heavy-lift brushless motors with large two-blade carbon-fiber propellers, straight arms from rectangular chassis, "
        "dark tinted semi-transparent half-cylinder canopy over central payload bay, full-sized medical stretcher with metal side rails visible, "
        "fixed 4-point tubular skid landing gear with neon-green multi-angle joint brackets, perimeter orange-red navigation LEDs, "
        "internal red-blue emergency strobes under canopy, downward white landing LEDs, realistic emergency response mood, cinematic dynamic camera movement, "
        "night city rooftop environment, preserve exact drone identity and proportions from reference image"
    )

    print("Loading I2V pipeline...")
    pipe = CogVideoXImageToVideoPipeline.from_pretrained(
        "THUDM/CogVideoX-5b-I2V", torch_dtype=torch.bfloat16
    ).to("cuda")
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()

    clips = []
    for i, ref in enumerate(refs, start=1):
        print(f"Generating {i}/{len(refs)} from {ref}...", flush=True)
        image = load_image(ref)
        frames = pipe(
            prompt=prompt,
            image=image,
            num_inference_steps=30,
            num_frames=41,
            guidance_scale=6.0,
            generator=torch.Generator("cpu").manual_seed(700 + i),
        ).frames[0]
        clip = f"spec_clip_{i}.mp4"
        export_to_video(frames, clip, fps=8)
        clips.append(clip)

    if len(clips) == 1:
        os.replace(clips[0], "drone_video_spec_asap.mp4")
        print("Done drone_video_spec_asap.mp4")
        return

    print("Stitching...")
    parts = [VideoFileClip(c) for c in clips]
    final = concatenate_videoclips(parts)
    final.write_videofile("drone_video_spec_asap.mp4", codec="libx264")
    print("Done drone_video_spec_asap.mp4")


if __name__ == "__main__":
    main()
