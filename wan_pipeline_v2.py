#!/usr/bin/env python3
"""
SW-1 Alpha — ViMax-Optimized Wan 2.2 14B Pipeline
===================================================
16 shots × 10 variants → stitched finals (80s @ 16fps)
Designed for NVIDIA H100 80GB HBM3

Usage:
    python wan_pipeline_v2.py --variant A         # Single variant
    python wan_pipeline_v2.py --variant ALL        # All 10 variants sequentially
    python wan_pipeline_v2.py --variant A --shot 5 # Single shot for testing
    python wan_pipeline_v2.py --variant A --fast   # Fewer diffusion steps (faster)

Variants:
    A = Standard Night       F = Arctic Blizzard
    B = Monsoon Storm         G = Desert Afternoon
    C = Golden Hour Dawn      H = IMAX Documentary
    D = Neon Cyberpunk        I = Film Noir B&W
    E = Handheld Documentary  J = Anime Stylized
"""

import os
import gc
import time
import torch
import argparse
import subprocess
from pathlib import Path
from diffusers import (
    WanPipeline,
    WanImageToVideoPipeline,
    AutoencoderKLWan,
    StableVideoDiffusionPipeline,
)
from diffusers.utils import export_to_video
from moviepy import VideoFileClip, concatenate_videoclips
from PIL import Image

# ============================================================================
# REFERENCE PHOTO MAPPING (for Image-to-Video shots)
# ============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent

REFERENCE_PHOTOS = {
    5: str(PROJECT_ROOT / "WhatsApp Image 2026-04-12 at 9.24.17 PM.jpeg"),
    6: str(PROJECT_ROOT / "WhatsApp Image 2026-04-12 at 9.24.17 PM.jpeg"),
    7: str(PROJECT_ROOT / "WhatsApp Image 2026-04-12 at 9.24.18 PM.jpeg"),
    8: str(PROJECT_ROOT / "WhatsApp Image 2026-04-12 at 9.24.18 PM (1).jpeg"),
    9: str(PROJECT_ROOT / "WhatsApp Image 2026-04-12 at 9.24.18 PM (2).jpeg"),
    11: str(PROJECT_ROOT / "WhatsApp Image 2026-04-12 at 9.24.19 PM.jpeg"),
    12: str(PROJECT_ROOT / "WhatsApp Image 2026-04-12 at 9.24.19 PM (1).jpeg"),
    14: str(PROJECT_ROOT / "WhatsApp Image 2026-04-12 at 9.24.19 PM (1).jpeg"),
    16: str(PROJECT_ROOT / "WhatsApp Image 2026-04-12 at 9.24.19 PM (2).jpeg"),
}

# ============================================================================
# 17 BASE PROMPTS — ViMax Motion-Agent Derived
# ============================================================================
BASE_PROMPTS = {
    1: "Photorealistic cinematic wide shot, six-lane divided city highway at night, sodium-vapor amber streetlights creating pools of warm light on wet asphalt, staggered traffic flowing left to right at 80 km/h with white headlight beams cutting through thin ground mist, glass-and-steel high-rise buildings on both sides with warm yellow lit windows creating vertical light columns, deep navy night sky with thin crescent moon at upper-left, concrete median barriers dividing opposing traffic, a red hatchback car in center lane suddenly swerving left and contacting the concrete median barrier, front bumper crumpling inward, windshield fracturing into radial web of white cracks, red plastic debris scattering across asphalt, trailing vehicles illuminating red brake lights in sequence, amber hazard lights beginning to flash on crashed vehicle, 16:9 cinematic aspect ratio, shallow depth of field, anamorphic lens flare",
    2: "Photorealistic cinematic medium shot, Indian male bystander mid-30s wearing light blue cotton button-down shirt with sleeves rolled to elbows and dark grey trousers, standing beside a white SUV at night on a highway shoulder, holding smartphone to right ear with cold white-blue screen glow illuminating the right side of his face, left hand extended outward palm-facing-traffic in a stop gesture, crashed red car with flashing amber hazard lights visible 15 meters behind him blurred in background, sodium amber streetlight overhead casting hard shadows downward, wet asphalt reflecting amber and red lights, distressed facial expression with furrowed brow and open mouth speaking urgently, 16:9 cinematic, dramatic side-lighting",
    3: "Photorealistic cinematic close-up shot, young Indian male late-20s with disheveled black hair matted with grey dust and a darkening purple bruise on left temple, slumped against deployed white airbag inside a crumpled car interior, eyes closed, thin line of blood from small cut above left eyebrow running down to cheekbone, grey torn t-shirt visible, seatbelt strap tight across chest, amber hazard light from outside flickering across his face through cracked windshield creating intermittent warm light, shallow breathing with chest barely rising, somber and urgent mood, shallow depth of field focused on face, dark interior car environment, 16:9 cinematic",
    4: "Photorealistic cinematic medium shot, Indian female emergency dispatch operator late-20s, dark navy uniform polo with red cross patch, thin-frame glasses, black hair in tight bun, wired headset, seated at curved desk in windowless control room. Large LED wall screen shows clean map data with a flashing red critical alert icon and pulsing route marker. Background monitors display abstract medical charts and waveform symbols only, no letters. Teal/amber glow, pressing red console button, 16:9 cinematic, cool blue-tinted lighting.",
    5: "Photorealistic cinematic wide shot, large black carbon-fiber octocopter medical drone (chassis must be blank, no alien text or 'SLLAO' written on it) sitting on a hospital rooftop concrete helipad at night, white circle with red H. Twelve flush-mounted orange LEDs around pad, eight dual-blade propellers spinning up, neon-green landing gear joints, transparent polycarbonate half-dome canopy with white stretcher visible inside, amber arm-tip LEDs turning green. Downwash blowing dust, city skyline background, 16:9 cinematic, upward-angle lighting.",
    6: "Photorealistic cinematic medium shot, two Indian male paramedics wearing fluorescent orange high-visibility vests over white medical uniforms with black rubber gloves and black boots, urgently sliding a white composite medical pod 1.8 meters long with rounded edges and red cross decal into the cargo bay underneath a large black carbon-fiber octocopter drone, propellers spinning above creating wind that ripples their vest fabric, neon-green landing gear joints visible at frame edges, spring-loaded metal latch clamps snapping shut with small green LED indicators illuminating beside each clamp, lead paramedic giving firm thumbs-up with right gloved hand while left hand presses vest flat against chest, night setting on hospital rooftop with amber city glow in background, 16:9 cinematic, action-lit from below by pad lights",
    7: "Photorealistic cinematic medium-wide shot from ground level looking upward, large black carbon-fiber octocopter medical drone lifting off vertically from hospital rooftop helipad, eight propellers spinning at high RPM creating motion-blurred translucent discs, powerful amber-tinted downwash rings radiating outward in concentric circles across concrete pad surface creating visible dust displacement, transparent dome canopy with white stretcher inside catching city light reflections, neon-green landing gear retracting upward, red and blue LED emergency light bar on top of canopy activating and casting rotating colored beams across rooftop, two paramedics in orange high-vis vests at pad edge leaning backward and shielding faces with raised forearms, green arm-tip LEDs blinking in forward sequence, drone ascending rapidly against city skyline of illuminated towers and deep navy night sky, 16:9 cinematic, dramatic low-angle perspective, motion blur on ascending drone",
    8: "Photorealistic cinematic extreme wide shot bird's-eye aerial view looking straight down, six-lane gridlocked highway completely filled with continuous ribbon of red tail-lights stretching in both directions, white-and-red traditional box ambulance trapped in traffic with roof emergency lights flashing but vehicle immobile, orange sodium streetlight grid pattern casting amber pools on congested roads, parallel side streets equally packed with vehicles, large black carbon-fiber octocopter medical drone with green LED arm lights and rotating red-blue emergency light bar flying 120 meters above the gridlock, transparent dome canopy visible from above, drone casting faint red-blue light reflections on vehicle rooftops below, orange GPS dotted trail line behind drone indicating flight path, sense of scale contrast between massive congestion below and free-flying drone above, 16:9 cinematic, overhead satellite-perspective, dramatic scale",
    9: "Photorealistic cinematic wide tracking shot from behind, large black carbon-fiber octocopter medical drone flying between two glass-curtain-wall skyscrapers at 18th-floor level at night, rotating red and blue emergency light reflections sweeping across both glass building facades creating moving colored streaks, warm yellow office window grid visible inside both towers, eight propellers motion-blurred into translucent discs, transparent polycarbonate dome canopy catching amber reflected city light revealing chrome stretcher rails inside, neon-green landing gear joints visible, speed-indicating wind-streak motion blur on building surfaces, deep navy night sky visible ahead between the towers, sense of speed and purpose and urgency, 16:9 cinematic, dynamic chase-camera perspective, anamorphic bokeh on background city lights",
    10: "Cinematic infographic split-panel design, left side silhouette of black octocopter medical drone with green LED dots and red-blue light bar, right side glowing teal cardiac ECG waveform. Use icon-only medical UI with numeric vitals, pulse dots, oxygen gauge, and heart symbol panels, no words or letters. Orange GPS path with ETA countdown rings, clean medical-tech aesthetic, 16:9 cinematic, high-tech HUD.",
    11: "Photorealistic cinematic extreme wide shot overhead bird's-eye view, hospital rooftop with large white circle and red H marking on concrete pad, twelve ground-mounted LED lights arranged in ring glowing green, large black carbon-fiber octocopter medical drone descending precisely toward pad center, eight propellers individually visible at reduced RPM decelerating from motion-blur to distinct blades, neon-green landing gear extended downward, transparent dome canopy with white medical stretcher visible, downwash fanning the teal surgical scrubs of three medical staff positioned at 3 o'clock 6 o'clock and 9 o'clock around the pad perimeter, small dust puffs erupting outward from each landing gear contact point, warm floodlight casting staff shadows outward, drone touching down on red H center, night sky above with distant city lights, 16:9 cinematic, dramatic top-down perspective",
    12: "Photorealistic cinematic medium shot, Indian female surgeon mid-40s in teal surgical scrubs with stethoscope around neck and hospital ID badge clipped to pocket, pressing red cargo-bay release lever on the right side of landed black carbon-fiber octocopter drone, spring-loaded latch clamps popping open, white composite medical pod being slid out from underneath drone platform by surgeon and two assistants, one assistant clipping portable cardiac monitor with teal screen and three lead wires onto pod left chrome rail, monitor displaying steady green heartbeat waveform, chrome-frame gurney positioned behind them ready to receive pod, hospital rooftop at night with green LED ring lights on pad visible in background, urgent coordinated movement with professional precision, 16:9 cinematic, dramatic medical-procedure lighting",
    13: "Photorealistic cinematic medium-wide shot, medical team of three in teal scrubs rapidly wheeling chrome-frame gurney with white medical pod through hospital rooftop toward open access doorway, warm golden light pouring outward from doorway interior creating dramatic backlit silhouette effect on the rushing team, cardiac monitor on gurney rail showing green waveform bouncing with gurney movement, large black octocopter medical drone visible on helipad behind them with green arm LEDs faintly glowing and transparent dome canopy open and empty, night sky above, motion blur on gurney wheels indicating speed, sense of urgency and life-saving purpose, 16:9 cinematic, golden-hour interior contrast with blue-night exterior",
    14: "Photorealistic cinematic medium shot, Indian female surgeon mid-40s in teal scrubs with surgical mask pulled down below chin revealing a slight smile of relief, right hand raised giving thumbs-up gesture with white latex glove, standing in bright white operating room with overhead surgical lights creating concentrated white beams, wall-mounted cardiac monitor behind her showing steady green waveform at 72 BPM and SpO2 99 percent in green digits, through glass observation window in background the distant hospital rooftop is visible with the silhouette of the black medical drone sitting on the pad with green LEDs blinking slowly, warm hopeful mood with professional satisfaction, 16:9 cinematic, high-key medical lighting with warm color grade",
    15: "Cinematic infographic side-by-side comparison on dark navy background. Left panel: traditional box ambulance icon, red congestion gridlock line and slow timer dial. Right panel: black octocopter medical drone icon with clear sky path and fast timer dial. Use icons, arrows, and numeric counters only, no words or letters. Data-driven comparison, 16:9 cinematic, bold design.",
    16: "Cinematic end card animation on deep navy background hex 1a1a2e. Centered flat silhouette icon of black octocopter medical drone with a soft green status pulse and circular beacon rings. Minimal icon-based broadcast-style ending, no text, no letters, no logos, 16:9 cinematic.",
}

# ============================================================================
# 10 VARIANT STYLE SUFFIXES — Each a completely distinct cinematic look
# ============================================================================
VARIANT_SUFFIXES = {
    # --- A: Standard Night ---
    "A": ", nighttime cinematography, deep navy and amber color palette, sodium-vapor streetlight warmth, wet asphalt surface reflections doubling all light sources, professional cinematic color grade with lifted blacks, subtle blue-teal shadows, anamorphic lens characteristics",
    # --- B: Monsoon Storm ---
    "B": ", heavy monsoon rain with visible diagonal rain streaks and water splashing on all surfaces, lightning flashes illuminating clouds in deep grey-purple sky, puddle reflections on roads doubling all lights into shimmering streaks, rain-soaked clothing and hair plastered to skin on all characters, wet glossy water beading on drone carbon fiber surfaces, dramatic thunder-storm atmosphere, water dripping from drone propeller tips, muted green-grey color grade",
    # --- C: Golden Hour Dawn ---
    "C": ", golden hour sunrise cinematography with warm orange-peach-pink sky gradient, long dramatic shadows stretching across all surfaces from low sun angle, lens flare from rising sun positioned low on horizon, golden warm rim-lighting on drone edges and character profiles creating bright halos, morning mist hovering at street level softening lower frame, cool blue shadows contrasting warm amber highlights, magic-hour film color grade with saturated oranges and deep blue skies",
    # --- D: Neon Cyberpunk ---
    "D": ", cyberpunk neon-lit nighttime aesthetic with bright magenta pink and electric cyan neon signs reflecting on wet road surfaces, holographic billboard advertisements on buildings casting colored light, electric blue accent lighting strips on drone body replacing standard LEDs, high-contrast noir lighting with crushed blacks and vivid neon highlights, steam and vapor rising from street grates creating volumetric atmosphere, chromatic aberration on edges, Blade Runner 2049 color grade with deep teal shadows and hot orange highlights",
    # --- E: Handheld Documentary ---
    "E": ", handheld documentary camera style with subtle natural camera shake and imperfect framing, available-light only with no dramatic artificial lighting, realistic mixed color temperature with warm sodium streetlights and cool fluorescent overheads, visible film grain texture overlay, naturalistic desaturated color grade with muted earth tones, news-footage broadcast authenticity feel, real-world urban India environment with Hindi street signage and auto-rickshaws visible",
    # --- F: Arctic Blizzard ---
    "F": ", arctic blizzard winter storm conditions with heavy white snowfall obscuring visibility, thick swirling snowflakes illuminated by drone LED lights creating volumetric white-blue cone beams, ice crystals forming on drone carbon-fiber arms and propeller edges, frost visible on windshields and road surfaces, all characters wearing heavy winter coats with visible breath vapor from mouths, pale blue-white desaturated color grade with cold steel-grey sky, frozen road surface with ice patches reflecting headlights, blizzard wind indicated by horizontal snow streak motion",
    # --- G: Desert Afternoon ---
    "G": ", harsh midday desert sun cinematography with bleached-out high-key lighting and extreme contrast hard shadows, dusty arid environment with sand-colored buildings and dry terrain, heat haze distortion shimmer visible on road surfaces and horizon line, drone kicking up fine orange-brown sand dust clouds from rotor downwash, squinting characters shielding eyes from intense sunlight, warm amber-yellow-ochre monotone color palette, deep blue cloudless sky, Middle-Eastern architectural elements with sandstone facades, lens dust particles visible in bright highlights",
    # --- H: IMAX Documentary ---
    "H": ", ultra-high-definition IMAX large-format documentary cinematography with extreme clarity and razor-sharp detail on every surface, stable tripod and gimbal-mounted smooth camera work, deep depth of field with everything in focus foreground to background, HDR dynamic range with preserved highlights in sky and deep shadow detail, neutral accurate color science with no stylistic color grading, clinical medical-documentary lighting that is bright and informative, professional broadcast-grade 4K sharpness, National Geographic production quality",
    # --- I: Film Noir Black & White ---
    "I": ", classic 1940s film noir black and white cinematography with high-contrast monochrome palette, deep black crushed shadows and bright blown-out highlights, dramatic venetian blind shadow patterns falling across character faces, single hard key light from high angles creating stark shadow geometry, wet reflective road surfaces creating mirror-like light pools, cigarette-smoke-style atmospheric haze catching light beams, vintage grain texture, Dutch angle tilted compositions, expressionist shadow play on walls and buildings",
    # --- J: Anime Stylized ---
    "J": ", Japanese anime art style with cel-shaded flat color rendering and bold black outlines on all objects and characters, vibrant saturated color palette with bright primary colors, dramatic anime speed lines radiating outward during drone flight sequences, exaggerated lens flare starburst effects on all light sources, stylized clouds with defined edges and gradients, character faces with large expressive anime-proportioned eyes, dynamic manga-inspired composition with diagonal framing, Studio Ghibli environmental detail with Makoto Shinkai sky rendering, sakura petals floating in wind",
}


# Shared drone design constraints from user reference to PREVENT MORPHING.
DRONE_SPEC_SUFFIX = ", MUST STRICTLY BE AN AUTONOMOUS HEAVY-LIFT MEDICAL OCTOCOPTER eVTOL. Flat octocopter architecture with 8 rotors in horizontal plane. Thick rectangular carbon-fiber core chassis. Exposed rigid cylindrical carbon-fiber tube sub-frame with red/black structural nodes. 8 heavy-lift brushless outrunner motors on extended straight arms. Large 2-blade carbon-fiber propellers. Dark-tinted semi-transparent aerodynamic barrel-vault canopy. Fixed 4-point tubular skid landing gear with neon-green joint brackets. Flashing red and blue emergency police strobes interior. ABSOLUTELY NO QUADCOPTERS, NO FIXED-WING AIRPLANES, NO SPACE SHUTTLES, NO CONSUMER DRONES, NO TILT-ROTORS. Maintain exact physical consistency of the black 8-rotor design."

DRONE_SHOTS = {5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16}

LANDSCAPE_SUFFIX = (
    ", horizontal landscape 16:9 aspect ratio, wide cinematic framing, "
    "width greater than height, no vertical portrait orientation or tall phone crop"
)

# 16:9 export resolution (landscape)
OUT_W, OUT_H = 1280, 720
OUTPUT_FPS = 16
TARGET_SECONDS = 80
LOOP_REPEATS = 12
# Wan-friendly 4n+1 per shot.
# 12 shots x 81 frames + 4 shots x 77 frames = 1280 total frames = 80.0s @ 16fps.
SHOT_FRAMES = {
    1: 81,
    2: 81,
    3: 81,
    4: 77,
    5: 81,
    6: 81,
    7: 81,
    8: 77,
    9: 81,
    10: 81,
    11: 81,
    12: 77,
    13: 81,
    14: 81,
    15: 81,
    16: 77,
}


def build_prompt(shot_id: int, variant_key: str) -> str:
    """Full prompt: base + style + optional drone canon + landscape lock."""
    p = BASE_PROMPTS[shot_id] + VARIANT_SUFFIXES[variant_key]
    if shot_id in DRONE_SHOTS:
        p += DRONE_SPEC_SUFFIX
    p += LANDSCAPE_SUFFIX
    return p


def free_memory():
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()


def get_gpu_info():
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        total = props.total_memory / (1024**3)
        return props.name, total
    return "No GPU", 0


def build_non_ending_loop(final_path: str, output_fps: int, repeats: int) -> str:
    """Create a long looped file so playback does not end quickly."""
    loop_path = final_path.replace(".mp4", f"_LOOP_x{repeats}.mp4")
    clip = VideoFileClip(final_path)
    repeated = concatenate_videoclips([clip] * repeats)
    repeated.write_videofile(loop_path, codec="libx264", fps=output_fps)
    repeated.close()
    clip.close()
    return loop_path


def generate_variant(variant_key, single_shot=None, fast: bool = False):
    gpu_name, gpu_mem = get_gpu_info()
    infer_steps = 18 if fast else 30
    print(f"🎬 SW-1 Alpha ViMax Pipeline — Variant {variant_key}")
    print(f"   GPU: {gpu_name}")
    print(f"   VRAM: {gpu_mem:.1f} GB")
    print(f"   Shots: {single_shot if single_shot else 'ALL 16'}")
    print(
        f"   Steps: {infer_steps} (fast={fast}) | {OUT_W}x{OUT_H} @ {OUTPUT_FPS}fps | {TARGET_SECONDS}s target"
    )
    print()

    out_dir = f"/home/variant_{variant_key}"
    os.makedirs(out_dir, exist_ok=True)

    # Determine which shots need I2V vs T2V
    shots_to_gen = [single_shot] if single_shot else sorted(BASE_PROMPTS.keys())
    i2v_shots = [
        s
        for s in shots_to_gen
        if s in REFERENCE_PHOTOS and os.path.exists(REFERENCE_PHOTOS[s])
    ]
    t2v_shots = [s for s in shots_to_gen if s not in i2v_shots]

    generated_clips = []

    # ---- Phase 1: T2V shots (text-to-video) ----
    if t2v_shots:
        print("📝 Phase 1: Loading T2V Pipeline...")
        vae = AutoencoderKLWan.from_pretrained(
            "Wan-AI/Wan2.2-T2V-A14B-Diffusers",
            subfolder="vae",
            torch_dtype=torch.float32,
        )
        pipe_t2v = WanPipeline.from_pretrained(
            "Wan-AI/Wan2.2-T2V-A14B-Diffusers",
            vae=vae,
            torch_dtype=torch.bfloat16,
        )
        pipe_t2v.enable_model_cpu_offload()

        for shot_id in t2v_shots:
            filename = os.path.join(out_dir, f"shot_{shot_id:02d}.mp4")
            if os.path.exists(filename):
                print(f"   ⏭️  Shot {shot_id}: Already exists, skipping.")
                generated_clips.append((shot_id, filename))
                continue

            prompt = build_prompt(shot_id, variant_key)
            n_frames = SHOT_FRAMES.get(shot_id, 81)

            print(f"\n🎬 T2V Shot {shot_id}/16 — {n_frames} frames")
            print(f"   Prompt: {prompt[:120]}...")

            t0 = time.time()
            output = pipe_t2v(
                prompt=prompt,
                num_frames=n_frames,
                height=OUT_H,
                width=OUT_W,
                num_inference_steps=infer_steps,
                guidance_scale=5.0,
                generator=torch.Generator("cpu").manual_seed(42 + shot_id),
            )
            export_to_video(output.frames[0], filename, fps=OUTPUT_FPS)
            elapsed = time.time() - t0
            print(f"   ✅ Saved in {elapsed:.0f}s → {filename}")
            generated_clips.append((shot_id, filename))
            free_memory()

        del pipe_t2v, vae
        free_memory()
        print("\n🧹 T2V pipeline unloaded.\n")

    # ---- Phase 2: I2V shots (image-to-video with reference photos) ----
    if i2v_shots:
        print("🖼️  Phase 2: Loading I2V Pipeline...")
        try:
            pipe_i2v = WanImageToVideoPipeline.from_pretrained(
                "Wan-AI/Wan2.2-I2V-14B-720P-Diffusers",
                torch_dtype=torch.bfloat16,
            )
            pipe_i2v.enable_model_cpu_offload()
            has_i2v = True
        except Exception as e:
            print(
                f"   ⚠️  I2V pipeline not available ({e}), falling back to Stable Video Diffusion image-to-video."
            )
            has_i2v = False
            pipe_fallback = StableVideoDiffusionPipeline.from_pretrained(
                "stabilityai/stable-video-diffusion-img2vid-xt",
                torch_dtype=torch.float16,
                variant="fp16",
            )
            pipe_fallback.enable_model_cpu_offload()

        for shot_id in i2v_shots:
            filename = os.path.join(out_dir, f"shot_{shot_id:02d}.mp4")
            if os.path.exists(filename):
                print(f"   ⏭️  Shot {shot_id}: Already exists, skipping.")
                generated_clips.append((shot_id, filename))
                continue

            prompt = build_prompt(shot_id, variant_key)
            n_frames = SHOT_FRAMES.get(shot_id, 81)
            ref_path = REFERENCE_PHOTOS[shot_id]

            print(f"\n🎬 I2V Shot {shot_id}/16 — {n_frames} frames")
            print(f"   Reference: {ref_path}")
            print(f"   Prompt: {prompt[:120]}...")

            t0 = time.time()
            if has_i2v:
                ref_image = Image.open(ref_path).convert("RGB").resize((OUT_W, OUT_H))
                output = pipe_i2v(
                    image=ref_image,
                    prompt=prompt,
                    num_frames=n_frames,
                    height=OUT_H,
                    width=OUT_W,
                    num_inference_steps=infer_steps,
                    guidance_scale=5.0,
                    generator=torch.Generator("cpu").manual_seed(42 + shot_id),
                )
            else:
                ref_image = Image.open(ref_path).convert("RGB").resize((1024, 576))
                svd_frames = max(14, min(25, n_frames // 3))
                output = pipe_fallback(
                    image=ref_image,
                    num_frames=svd_frames,
                    num_inference_steps=infer_steps,
                    decode_chunk_size=8,
                    motion_bucket_id=127,
                    noise_aug_strength=0.02,
                    generator=torch.Generator("cpu").manual_seed(42 + shot_id),
                )

            export_to_video(output.frames[0], filename, fps=OUTPUT_FPS)
            elapsed = time.time() - t0
            print(f"   ✅ Saved in {elapsed:.0f}s → {filename}")
            generated_clips.append((shot_id, filename))
            free_memory()

        if has_i2v:
            del pipe_i2v
        else:
            del pipe_fallback
        free_memory()
        print("\n🧹 I2V pipeline unloaded.\n")

    # ---- Phase 3: Stitch final movie ----
    generated_clips.sort(key=lambda x: x[0])
    clip_paths = [c[1] for c in generated_clips if os.path.exists(c[1])]

    if len(clip_paths) >= 2:
        print(f"[>] Stitching {len(clip_paths)} shots into final movie...")
        final_path = os.path.join(
            out_dir, f"FINAL_SW1_VARIANT_{variant_key}_{TARGET_SECONDS}s.mp4"
        )
        clips = [VideoFileClip(p) for p in clip_paths]
        final = concatenate_videoclips(clips)
        if final.duration > TARGET_SECONDS:
            final = final.subclipped(0, TARGET_SECONDS)
        final.write_videofile(final_path, codec="libx264", fps=OUTPUT_FPS)
        for c in clips:
            c.close()
        duration = final.duration
        final.close()
        print(f"[OK] VARIANT {variant_key} COMPLETE -> {final_path}")
        print(f"     Duration: {duration:.1f}s | Shots: {len(clip_paths)}")

        print(f"[^] Building non-ending loop file (x{LOOP_REPEATS})...")
        loop_path = build_non_ending_loop(final_path, OUTPUT_FPS, LOOP_REPEATS)
        print(f"[OK] Loop file -> {loop_path}")

        # ---- Phase 4: Upload to transfer.sh for easy retrieval ----
        print(f"[^] Uploading VARIANT {variant_key} files to transfer.sh...")
        fname_final = f"SW1_VARIANT_{variant_key}_{TARGET_SECONDS}s.mp4"
        fname_loop = f"SW1_VARIANT_{variant_key}_LOOP_x{LOOP_REPEATS}.mp4"
        try:
            result_final = subprocess.run(
                [
                    "curl",
                    "--upload-file",
                    final_path,
                    f"https://transfer.sh/{fname_final}",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )
            result_loop = subprocess.run(
                [
                    "curl",
                    "--upload-file",
                    loop_path,
                    f"https://transfer.sh/{fname_loop}",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )
            download_url_final = result_final.stdout.strip()
            download_url_loop = result_loop.stdout.strip()
            if download_url_final.startswith("http") and download_url_loop.startswith(
                "http"
            ):
                print(f"")
                print(f"  ============================================================")
                print(f"  DOWNLOAD URL — VARIANT {variant_key} ({variant_key})")
                print(f"  Final 80s: {download_url_final}")
                print(f"  Loop x{LOOP_REPEATS}: {download_url_loop}")
                print(f"  ============================================================")
                print(f"")
                # Write URL to a local file for easy retrieval
                url_file = os.path.join(
                    out_dir, f"download_url_variant_{variant_key}.txt"
                )
                with open(url_file, "w") as f:
                    f.write(f"Variant {variant_key}\n")
                    f.write(f"Style: {VARIANT_NAMES.get(variant_key, variant_key)}\n")
                    f.write(f"Final {TARGET_SECONDS}s URL: {download_url_final}\n")
                    f.write(f"Loop x{LOOP_REPEATS} URL: {download_url_loop}\n")
                    f.write(f"Final file: {final_path}\n")
                    f.write(f"Loop file: {loop_path}\n")
            else:
                print(f"[!] Final upload response: {result_final.stdout[:200]}")
                print(f"[!] Final stderr: {result_final.stderr[:200]}")
                print(f"[!] Loop upload response: {result_loop.stdout[:200]}")
                print(f"[!] Loop stderr: {result_loop.stderr[:200]}")
        except Exception as e:
            print(f"[!] Upload failed: {e}")
            print(f"    Files are still on disk at: {final_path} and {loop_path}")
    else:
        print(f"[!] Only {len(clip_paths)} clips generated, skipping stitch.")

    return out_dir


ALL_VARIANTS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
VARIANT_NAMES = {
    "A": "Standard Night",
    "B": "Monsoon Storm",
    "C": "Golden Hour Dawn",
    "D": "Neon Cyberpunk",
    "E": "Handheld Documentary",
    "F": "Arctic Blizzard",
    "G": "Desert Afternoon",
    "H": "IMAX Documentary",
    "I": "Film Noir B&W",
    "J": "Anime Stylized",
}


def main():
    parser = argparse.ArgumentParser(description="SW-1 Alpha ViMax Wan 2.2 Pipeline")
    parser.add_argument(
        "--variant",
        type=str,
        default="A",
        choices=ALL_VARIANTS + ["ALL"],
        help="Which variant to generate (A-J or ALL)",
    )
    parser.add_argument(
        "--shot",
        type=int,
        default=None,
        help="Generate only a specific shot number (1-16)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fewer diffusion steps (recommended for faster JarvisLabs turnaround)",
    )
    args = parser.parse_args()

    if args.variant == "ALL":
        for v in ALL_VARIANTS:
            print(f"\n{'=' * 60}")
            print(f"  STARTING VARIANT {v} — {VARIANT_NAMES[v]}")
            print(f"{'=' * 60}\n")
            generate_variant(v, args.shot, fast=args.fast)
        print("\n🎉 ALL VARIANTS GENERATION COMPLETE!")
    else:
        print(f"\n  VARIANT {args.variant} — {VARIANT_NAMES[args.variant]}\n")
        generate_variant(args.variant, args.shot, fast=args.fast)
        print(f"\n🎉 VARIANT {args.variant} GENERATION COMPLETE!")


if __name__ == "__main__":
    main()
