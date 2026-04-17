# Project Guidelines & Secrets Handover

This document contains the complete context, configurations, API keys, and SSH details for the current active projects to hand over to another AI assistant. No details have been omitted.

## 1. JarvisLabs GPU Infrastructure

### SSH Remote Access (Active Instance)
- **User:** `root`
- **Host:** `sshe.jarvislabs.ai`
- **Port:** `11114`

### JarvisLabs API Keys
Multiple keys were rotated / utilized across the active scripts:
- Key 1 (from `watchdog.ps1`): `ljpVQf3s1lYuJP-oPrTKnbbFL7bPBvbzTUx0EH_kC1U`
- Key 2 (from `run_jl.py`): `Z9TRPZhaPtlT1Ptd9m6f6pjKGIkWivG741tmc4aFHnw`
- Key 3 (from `manage_jl.py`): `mgMHYQlRZqsDXo988uk1Ux4uzRxTeXAxScvRNU3QTgA`

### Framework & Workflow
- The JarvisLabs CLI (`jl`) is actively being used to auto-deploy `.py` pipelines (`run_jl.py`, `manage_jl.py`).
- **Flags utilized on run**: `--gpu H100`, `--storage 300`, `--follow`, `--destroy`, `--yes`.

## 2. Active Projects Workspace

**Path:** `c:\happy horse`

### Core Pipelines (Text-to-Video generation using Open Source Models)
- **Goal:** Successfully generating 10 continuous cinematic variants for an AI story ("happy horse"). 16-shot sequences are generated and stitched into a final MP4 movie.
- **Models utilized:** Wan 2.2 / 2.7 series, CogVideoX-5b, and HappyHorse API (though the goal is moving completely to local/self-hosted deployment on H100 instances to save inference credits).
- **Scripts:**
  - `launch_10_variants.py`: Orchestrator script.
  - `wan_pipeline_v2.py`: The actual inference execution script.
  - `dashboard_server.py`: Running a local web-server for status.
  - `gen_single_shot.py`, `rescue_uncompleted.py`, `rescue_videos.py`: Failsafe and recovery scripts for instance failures.
  - `watchdog.ps1`: Used for instance logging and retrieval of files via SCP to bypass instance terminations (`FINAL_SW1_MOVIE.mp4`).

## 3. Other Historical Projects Context

### Azure VM Autonomous Backend
- Deploying a fully autonomous agent (OpenHands) on Azure VMs.
- Driven by a fast local "Gemma model" combined with the Google AI Studio API for cost-effective inference tracking.

### Meta Quest 3S Monitoring
- 360-degree remote monitoring pipeline.
- Specifically focused on overlapping CAD digital twins on top of real-time worksite streams for VR headsets.

### Air Taxi 3D Simulator
- 3D interactive web project with horizontal layout.
- Animating 16 coaxial rotors, mobile dual-joystick physics controls, and live telemetry scanning via a shareable QR code for a connected web dashboard.

### Web Browser Automation
- Local use of the Steel Browser Automation SDK in Node.js to manage local Chrome environments efficiently, particularly bypassing some CLI issues. Used initially for an "attendance tracker" portal automation spanning multiple college subjects.
