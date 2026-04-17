import requests
import time

API_KEY = "mgMHYQlRZqsDXo988uk1Ux4uzRxTeXAxScvRNU3QTgA"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
BASE_URL = "https://api.jarvislabs.ai"


def get_instances_with_retry(max_attempts=5, timeout=20):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                f"{BASE_URL}/instances/", headers=HEADERS, timeout=timeout
            )
            if response.status_code == 200:
                return response.json()
            last_error = f"HTTP {response.status_code}: {response.text[:300]}"
        except Exception as e:
            last_error = str(e)

        if attempt < max_attempts:
            wait_s = min(2 * attempt, 10)
            print(f"Retry {attempt}/{max_attempts} after error: {last_error}")
            time.sleep(wait_s)

    raise RuntimeError(last_error or "Unknown API error")


def investigate():
    print("--- Detailed GPU Instance Audit ---")
    try:
        instances = get_instances_with_retry()
    except Exception as e:
        print(f"Error: {e}")
        return

    if not instances:
        print("No instances found at all.")
        return

    for inst in instances:
        name = inst.get("name", "unnamed")
        inst_id = inst.get("instance_id")
        status = inst.get("status")
        gpu_type = inst.get("gpu_type")

        print(f"\nInstance Found: {name}")
        print(f"  ID: {inst_id} | Status: {status} | GPU: {gpu_type}")

        # Determine if it's "Useful"
        if status == "Running":
            if name.startswith("fix-"):
                print(
                    "  Verdict: FAILED REFINEMENT instance. (Stalled due to missing rsync)"
                )
            elif name == "jl-run":
                print("  Verdict: Legacy/Stalled run instance.")
            else:
                print(
                    "  Verdict: Unknown purpose. Please verify if you started this manually."
                )
        else:
            print(f"  Verdict: {status} (Not active)")


if __name__ == "__main__":
    investigate()
