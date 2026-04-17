import os
import re
from jarvislabs.cli.app import app
from typer.testing import CliRunner

os.environ["JL_API_KEY"] = "mgMHYQlRZqsDXo988uk1Ux4uzRxTeXAxScvRNU3QTgA"

def main():
    print("Fetching active instances via Typer CliRunner...")
    runner = CliRunner()
    result = runner.invoke(app, ["list"])
    
    # Ensure stdout is parsed
    out = result.stdout
    # Extract all 5-7 digit instance IDs from the table string
    ids = re.findall(r"│\s*(\d{5,7})\s*│", out)
    unique_ids = list(set(ids))
    
    if not unique_ids:
        print("No instances found.")
        return
        
    print(f"Found {len(unique_ids)} unique instances. Destroying them now...")
    
    for iid in unique_ids:
        print(f"Destroying instance {iid}...")
        # Assume there's a --yes or -y flag or we might just use standard input
        try:
            # We can pass standard input via input="y\n" to the runner
            res = runner.invoke(app, ["destroy", iid], input="y\n")
            if res.exception:
                print(f"Error destroying {iid}: {res.exception}")
            else:
                print(f"Success for {iid}.")
        except Exception as e:
            print(f"Failed manually on {iid}: {e}")

    print("Cleanup complete!")

if __name__ == "__main__":
    main()
