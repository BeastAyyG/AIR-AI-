# AIR-AI-

> AI-powered autonomous drone inspection & reconnaissance system with real-time dashboard and log analysis

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)
![ArduPilot](https://img.shields.io/badge/ArduPilot-Integrated-blue?style=flat-square)

## Overview

AIR-AI is an AI-powered system for autonomous drone inspection and reconnaissance. It includes real-time telemetry monitoring, log analysis, flight variant calibration, and an automated emergency cleanup system.

## Features

- Real-time drone dashboard (HTML/Python server)
- Flight log analysis and variant checking
- GPS coordinate calibration
- Emergency cleanup automation
- Text-to-Video generation via JarvisLabs CLI (CogVideoX-5b)
- Remote MAVLink connection support

## Key Files

| File | Purpose |
|------|---------|
| `dashboard_server.py` | Real-time monitoring server |
| `check_logs.py` | Flight log analyzer |
| `calibrate_coords.py` | GPS calibration tool |
| `emergency_cleanup.py` | Auto emergency response |
| `check_variants.py` | Drone variant checker |

## Getting Started

```bash
git clone https://github.com/BeastAyyG/AIR-AI-.git
cd AIR-AI-
pip install -r requirements.txt
python dashboard_server.py
```

## Tech Stack

- **Python** - Core system logic
- **HTML/JS** - Dashboard frontend
- **MAVLink** - Drone communication protocol
- **ArduPilot** - Flight controller integration

## Author

**BeastAyyG** - [GitHub](https://github.com/BeastAyyG)
