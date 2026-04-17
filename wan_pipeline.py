import torch
import os
import gc
from diffusers import AutoencoderKLWan, WanPipeline
from diffusers.utils import export_to_video
from moviepy import VideoFileClip, concatenate_videoclips

prompts = {
    1: "Kurzgesagt flat 2D animation, peaceful night city highway, cartoon cars driving smoothly, warm yellow windows on skyscrapers, deep navy sky with small white star dots, one red cartoon car driving normally in center lane, calm ambient mood, thick outlines, soft amber streetlights, slow camera pan following traffic, 16:9",
    2: "Kurzgesagt flat 2D animation, sudden highway collision, red cartoon car swerving and hitting barrier, bold cartoon impact explosion burst in orange and yellow, car crumpled with Kurzgesagt impact star shapes, skid mark lines on road, other cartoon cars braking hard with red brake glow, debris pieces flying outward as flat geometric shapes, dramatic zoom in, thick outlines, deep navy background, 16:9",
    3: "Kurzgesagt flat 2D animation, panicked cartoon bystander character standing outside car, round eyes wide open in shock, holding phone up calling emergency, glowing red phone screen with 112 dialing, speech bubble with exclamation mark, crashed car smoking behind them with cartoon smoke puffs, amber hazard lights flashing on other cars, thick outlines, urgent mood, deep navy, 16:9",
    4: "Kurzgesagt flat 2D animation, close-up of injured cartoon character slumped in crumpled car seat, small pain stars around head, faded color on character showing unconscious state, cracked windshield shown as geometric shard shapes, red ambulance light reflection flickering on face, small heartbeat line icon fading in corner showing weak pulse, thick outlines, somber mood, deep navy, 16:9",
    5: "Kurzgesagt flat 2D animation, emergency dispatch control room, three cartoon operators at glowing screens, large central map screen showing city grid with red blinking dot marking accident location, one operator pointing urgently at screen, bold red alert banner reading 'CRITICAL TRAUMA — HIGHWAY 4', teal and amber monitor glow lighting faces, motion lines showing urgency, thick outlines, deep navy, 16:9",
    6: "Kurzgesagt flat 2D animation, SW-1 Alpha drone sitting on hospital rooftop launchpad in standby mode, gray dim LEDs suddenly switching to bright green one by one, propellers twitching then beginning to spin, orange launchpad lights activating in sequence, bold electric spark lines around motors showing power surge, cartoon city skyline behind, upward zoom slowly starting, thick outlines, deep navy sky, 16:9",
    7: "Kurzgesagt flat 2D animation, two cartoon paramedics in bright orange vests urgently sliding white rounded medical pod into SW-1 Alpha drone underside bay, motion speed lines on arms showing fast movement, green lock click with checkmark bubble appearing, status panel switching red to green, one paramedic giving thumbs up with determined face, emergency blue and red glow sweeping rooftop, thick outlines, bold flat, deep navy, 16:9",
    8: "Kurzgesagt flat 2D animation, dramatic SW-1 Alpha liftoff, powerful amber downwash rings blasting outward in concentric circles, both paramedics shielding faces leaning backward with motion lines, drone rising fast with upward speed streaks, green LED arm lights blinking in sequence, bold golden city skyline below getting smaller, camera pulling back and tilting upward revealing full city, thick outlines, deep navy sky, 16:9",
    9: "Kurzgesagt flat 2D animation, split screen moment, bottom half shows completely gridlocked cartoon highway with red tail-lights stretching endlessly, traditional ambulance cartoon stuck in traffic with frustrated emoji face, top half shows SW-1 Alpha drone flying freely above it all, bold arrow showing drone path versus blocked road path, thick outlines, amber and red color contrast, deep navy background, 16:9",
    10: "Kurzgesagt flat 2D animation, chase camera behind SW-1 Alpha drone flying fast above cartoon city, warm amber and yellow building windows rushing past on both sides, speed lines streaming backward, GPS route shown as glowing orange dotted trail ahead curving toward hospital red cross icon in distance, green LED dots on drone arms blinking, dramatic sense of speed and purpose, thick outlines, deep navy sky, 16:9",
    11: "Kurzgesagt flat 2D infographic animation, split panel design, left side shows SW-1 Alpha flying silhouette, right side shows glowing teal heartbeat line pulsing, amber readout panels showing SpO2 97%, Heart Rate 78 BPM, Temperature 36.8C, small cartoon doctor icon at hospital viewing same data on tablet in real time, connecting signal waves between drone and doctor, orange GPS trail with ETA countdown 01:42, thick outlines, bold flat design, deep navy, 16:9",
    12: "Kurzgesagt flat 2D animation, overhead bird's eye view of hospital rooftop, large glowing H landing pad with orange guide lights activating one by one as SW-1 Alpha descends from above getting larger, three cartoon doctors and nurses rushing into position around pad edges arms ready, bold circular glow expanding from pad center, dramatic top-down zoom, thick outlines, bold flat illustration, deep navy night, 16:9",
    13: "Kurzgesagt flat 2D animation, SW-1 Alpha drone landing precisely on hospital pad, propeller motion arcs slowing from fast blur to stop, landing gear touching pad with small impact ring puff, orange guide lights turning green in sequence outward from center, medical team rushing in from all sides with motion lines, bold 'LANDED' checkmark bubble appearing above drone, thick outlines, relief mood, deep navy, 16:9",
    14: "Kurzgesagt flat 2D animation, doctors urgently pulling white medical pod from SW-1 Alpha hatch, one cartoon doctor immediately attaching glowing teal monitor showing steady heartbeat, another rushing gurney forward, warm golden hospital door light pouring outward behind them creating silhouette effect, red cross symbol glowing on pod, motion speed lines on all characters showing urgency, thick outlines, bold flat, 16:9",
    15: "Kurzgesagt flat 2D animation, hospital operating room, cartoon surgeon giving thumbs up with big smile, patient cartoon character on bed with small floating heart above showing alive, green heartbeat line steady and bold on monitor, warm golden room light, relief emoji reactions floating from medical team, small SW-1 Alpha drone silhouette visible through window in background still on rooftop, thick outlines, warm hopeful mood, deep navy to warm gold color shift, 16:9",
    16: "Kurzgesagt flat 2D infographic animation, bold side by side comparison panel, left shows traditional ambulance icon with timer reading 34 MINUTES stuck in traffic cartoon, right shows SW-1 Alpha drone icon with timer reading 7 MINUTES flying free above city, massive bold red X on ambulance side, bold green checkmark on drone side, animated timer counting down both simultaneously, thick outlines, amber and teal color coding, deep navy background, Kurzgesagt data style, 16:9",
    17: "Kurzgesagt end card animation, deep navy #1a1a2e background, SW-1 Alpha flat drone icon centered top with single blinking green LED, white bold text fading in below 'SW-1 ALPHA', smaller amber text underneath 'The sky is the fastest road to survival', thin white line underneath, subtle upward floating motion on icon, clean minimal Kurzgesagt signature style, smooth fade in sequence, 16:9"
}

def free_memory():
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()

def main():
    print("🎬 Wan 2.2 14B 17-SHOT PIPELINE — Loading models...")
    
    # Load VAE
    vae = AutoencoderKLWan.from_pretrained(
        "Wan-AI/Wan2.2-T2V-A14B-Diffusers",
        subfolder="vae",
        torch_dtype=torch.float32,
    )
    
    # Load pipeline
    pipe = WanPipeline.from_pretrained(
        "Wan-AI/Wan2.2-T2V-A14B-Diffusers",
        vae=vae,
        torch_dtype=torch.bfloat16,
    )
    pipe.to("cuda")
    pipe.enable_model_cpu_offload()

    generated_clips = []
    
    for shot_id, prompt in prompts.items():
        filename = f"/home/out_shot_{shot_id}.mp4"
        generated_clips.append(filename)
        
        if os.path.exists(filename):
            print(f"Skipping Shot {shot_id}: Already exists.")
            continue
            
        print(f"\n🎬 Generating Shot {shot_id}/17...")
        print(f"   Prompt: {prompt[:100]}...")
        
        output = pipe(
            prompt=prompt,
            num_frames=81, 
            height=720,
            width=1280,
            num_inference_steps=30,
            guidance_scale=5.0,
            generator=torch.Generator("cpu").manual_seed(42),
        )
        
        export_to_video(output.frames[0], filename, fps=16)
        print(f"✅ Saved Shot {shot_id} to {filename}")
        
        free_memory()

    # Memory cleanup before stitching
    del pipe
    del vae
    free_memory()

    print("\n🎞️ Stitching final cinematic masterpiece...")
    clips = [VideoFileClip(c) for c in generated_clips]
    final_video = concatenate_videoclips(clips)
    final_video.write_videofile("/home/FINAL_WAN22_MOVIE.mp4", codec="libx264")
    print("✅ All done! Movie saved as FINAL_WAN22_MOVIE.mp4")

if __name__ == "__main__":
    main()
