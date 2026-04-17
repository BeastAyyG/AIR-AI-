import subprocess
import re
import os

def main():
    print("Fetching active instances...")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf8"
    
    try:
        out = subprocess.check_output("python manage_jl.py list", shell=True, text=True, env=env)
    except Exception as e:
        print("Failed to get list.")
        return

    # Extract all 6-digit instance IDs from the table
    ids = re.findall(r"│\s*(\d{5,7})\s*│", out)
    unique_ids = list(set(ids))
    
    if not unique_ids:
        print("No instances found.")
        return
        
    print(f"Found {len(unique_ids)} instances. Destroying them now...")
    
    for iid in unique_ids:
        print(f"Destroying instance {iid}...")
        # We pipe 'y' to the command just in case it asks for confirmation
        subprocess.run(f"echo y | python manage_jl.py destroy {iid}", shell=True, env=env)

    print("Cleanup complete!")

if __name__ == "__main__":
    main()
