import requests
import time

API_KEY = "mgMHYQlRZqsDXo988uk1Ux4uzRxTeXAxScvRNU3QTgA"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
BASE_URL = "https://api.jarvislabs.ai"


def request_with_retry(method, url, max_attempts=5, timeout=20):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.request(method, url, headers=HEADERS, timeout=timeout)
            if resp.status_code in (200, 201, 202, 204):
                return resp
            last_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
        except Exception as e:
            last_error = str(e)

        if attempt < max_attempts:
            wait_s = min(2 * attempt, 10)
            print(f"  Retry {attempt}/{max_attempts} after error: {last_error}")
            time.sleep(wait_s)

    raise RuntimeError(last_error or "Unknown API error")


def get_instances(max_attempts=5):
    resp = request_with_retry(
        "GET", f"{BASE_URL}/instances/", max_attempts=max_attempts
    )
    return resp.json()


def delete_instance(instance_id, max_attempts=6):
    primary = f"{BASE_URL}/instances/{instance_id}"
    legacy = f"{BASE_URL}/instances/?instance_id={instance_id}"

    try:
        request_with_retry("DELETE", primary, max_attempts=max_attempts)
        return True, "deleted via /instances/{id}"
    except Exception as first_error:
        try:
            request_with_retry("DELETE", legacy, max_attempts=max_attempts)
            return True, "deleted via /instances/?instance_id="
        except Exception as second_error:
            return (
                False,
                f"primary failed: {first_error}; fallback failed: {second_error}",
            )


def cleanup():
    print("--- Emergency API Cleanup ---")

    # List instances
    try:
        instances = get_instances()
    except Exception as e:
        print(f"Error fetching instances: {e}")
        return

    total_targets = 0
    deleted = 0
    failed = 0

    for inst in instances:
        name = inst.get("name", "unnamed")
        inst_id = inst.get("instance_id")

        if name.startswith("fix-") or name == "jl-run":
            total_targets += 1
            print(f"Deleting Instance: {name} (ID: {inst_id})")
            ok, details = delete_instance(inst_id)
            if ok:
                deleted += 1
                print(f"  Result: Success ({details})")
            else:
                failed += 1
                print(f"  Result: Failed ({details})")

    if total_targets == 0:
        print("No targets found.")
        return

    # Verify remaining targets after deletion pass.
    try:
        remaining = [
            inst
            for inst in get_instances(max_attempts=3)
            if inst.get("name", "").startswith("fix-") or inst.get("name") == "jl-run"
        ]
    except Exception as e:
        remaining = None
        print(f"WARNING: Could not verify final state due to API error: {e}")

    if remaining is None:
        print(
            f"Done. Requested cleanup for {total_targets} targets (success={deleted}, failed={failed})."
        )
    elif remaining:
        print(
            f"Done. Requested cleanup for {total_targets} targets (success={deleted}, failed={failed})."
        )
        print(
            f"WARNING: {len(remaining)} target instances still present after cleanup:"
        )
        for inst in remaining:
            print(
                f"  - {inst.get('name', 'unnamed')} | {inst.get('instance_id')} | {inst.get('status')}"
            )
    else:
        print(f"Done. Cleaned all {total_targets} target instances successfully.")


if __name__ == "__main__":
    cleanup()
