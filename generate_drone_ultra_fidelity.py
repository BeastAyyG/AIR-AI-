import os

import torch
from diffusers import CogVideoXImageToVideoPipeline
from diffusers.utils import export_to_video, load_image


def choose_ref():
    for path in ["reference_drone.png", "ref1.jpeg", "ref2.jpeg", "ref3.jpeg"]:
        if os.path.exists(path):
            return path
    raise RuntimeError("No reference image found")


def main():
    ref = choose_ref()
    print(f"Using reference: {ref}")

    prompt = (
        "Ultra-realistic heavy-lift medical evacuation octocopter eVTOL, exact reference-locked design. "
        "Flat octocopter architecture with 8 rotors in one horizontal plane around a thick rectangular carbon-fiber central chassis. "
        "Rigid cylindrical carbon-fiber tube sub-frame with block structural nodes, heavy-lift brushless motors, large two-blade propellers. "
        "Dark tinted semi-transparent half-cylinder canopy covering a full medical stretcher with metal side rails. "
        "Fixed 4-point tubular skid landing gear with neon-green joint brackets. Orange-red nav beacons, internal red-blue emergency strobes, downward white landing lights. "
        "Preserve exact body shape, proportions, and geometry from the reference image with minimal deformation. "
        "Cinematic rooftop takeoff and fly-by at night, controlled camera motion, crisp details, photoreal, high consistency"
    )

    print("Loading I2V pipeline...")
    pipe = CogVideoXImageToVideoPipeline.from_pretrained(
        "THUDM/CogVideoX-5b-I2V", torch_dtype=torch.bfloat16
    ).to("cuda")
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()

    image = load_image(ref)
    print("Generating ultra-fidelity single take...")
    frames = pipe(
        prompt=prompt,
        image=image,
        num_inference_steps=42,
        num_frames=57,
        guidance_scale=7.0,
        generator=torch.Generator("cpu").manual_seed(1337),
    ).frames[0]

    export_to_video(frames, "drone_video_ultra_fidelity.mp4", fps=8)
    print("Done drone_video_ultra_fidelity.mp4")


if __name__ == "__main__":
    main()
