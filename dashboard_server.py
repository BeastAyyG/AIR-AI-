"""
SW-1 Alpha — Live Render Dashboard Server
Run: python dashboard_server.py
Then open: http://localhost:8765
"""
import json, os, subprocess, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
STATUS_FILE = ROOT / "variant_status.json"
API_KEY = "mgMHYQlRZqsDXo988uk1Ux4uzRxTeXAxScvRNU3QTgA"

# Run IDs from the launcher logs
RUN_IDS = {
    "A": "r_44e833d7",
    "B": "r_522c2591",
    "C": "r_584ef55e",
    "D": "r_e7c789c7",
    "E": "r_d570e3dd",
    "F": "r_76e51e69",
    "G": "r_23393e74",
    "H": "r_431be14a",
    "I": "r_8a8fce05",
    "J": "r_466f954d",
}

STYLE_NAMES = {
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

GPU_TYPE = {
    "A": "H100", "B": "H100", "E": "H100", "F": "H100", "J": "H100",
    "C": "A100", "D": "A100", "H": "A100", "I": "A100",
    "G": "A6000",
}

live_status = {}

def poll_jl_status():
    """Background thread: poll JarvisLabs every 30s for each run."""
    env = os.environ.copy()
    env["JL_API_KEY"] = API_KEY
    while True:
        for var, run_id in RUN_IDS.items():
            try:
                result = subprocess.run(
                    ["jl", "run", "status", run_id],
                    capture_output=True, text=True, env=env, timeout=15
                )
                output = result.stdout + result.stderr
                state = "running"
                cost = "—"
                shot = "—"
                for line in output.splitlines():
                    if "State:" in line:
                        state = line.split("State:")[-1].strip()
                    if "Instance cost:" in line:
                        cost = line.split("Instance cost:")[-1].strip()
                    if "Shot" in line and "/" in line:
                        shot = line.strip()

                live_status[var] = {
                    "style": STYLE_NAMES[var],
                    "gpu": GPU_TYPE[var],
                    "run_id": run_id,
                    "state": state,
                    "cost": cost,
                    "last_log": shot,
                    "ts": time.strftime("%H:%M:%S"),
                }
            except Exception as e:
                live_status[var] = {
                    "style": STYLE_NAMES[var],
                    "gpu": GPU_TYPE[var],
                    "run_id": run_id,
                    "state": "unknown",
                    "cost": "—",
                    "last_log": str(e),
                    "ts": time.strftime("%H:%M:%S"),
                }

        # Also merge in local variant_status.json if available
        if STATUS_FILE.exists():
            try:
                with open(STATUS_FILE) as f:
                    local = json.load(f)
                for var, info in local.items():
                    if var in live_status:
                        local_state = info.get("status", "").upper()
                        if "COMPLETE" in local_state or "ERROR" in local_state:
                            live_status[var]["state"] = local_state.lower()
                        live_status[var]["last_log"] = info.get("last_log", live_status[var]["last_log"])
            except Exception:
                pass

        time.sleep(30)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass  # silence default logs

    def do_GET(self):
        if self.path == "/status":
            data = json.dumps({"variants": live_status, "ts": time.strftime("%H:%M:%S")})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data.encode())
        elif self.path in ("/", "/index.html"):
            html_path = ROOT / "dashboard.html"
            if html_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html_path.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    # Pre-populate with base info so dashboard loads instantly
    for var in RUN_IDS:
        live_status[var] = {
            "style": STYLE_NAMES[var], "gpu": GPU_TYPE[var],
            "run_id": RUN_IDS[var], "state": "polling...",
            "cost": "—", "last_log": "Connecting to JarvisLabs...",
            "ts": time.strftime("%H:%M:%S"),
        }

    t = threading.Thread(target=poll_jl_status, daemon=True)
    t.start()

    PORT = 8765
    server = HTTPServer(("localhost", PORT), Handler)
    print(f"\n[OK] Dashboard running at: http://localhost:{PORT}")
    print("   Auto-polls JarvisLabs every 30 seconds.")
    print("   Press Ctrl+C to stop.\n")
    webbrowser.open(f"http://localhost:{PORT}")
    server.serve_forever()
