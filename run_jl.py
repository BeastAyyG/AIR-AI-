import sys
import os

os.environ["JL_API_KEY"] = "Z9TRPZhaPtlT1Ptd9m6f6pjKGIkWivG741tmc4aFHnw"

from jarvislabs.cli.app import main
sys.argv = [
    "jl", "run", "generate_hh.py",
    "--gpu", "H100",
    "--storage", "300",
    "--name", "wan22-h100",
    "--requirements", "requirements_hh.txt",
    "--follow",
    "--destroy",
    "--yes",
    "--",
    "--prompt", "A cinematic shot of a happy horse running through a beautiful green meadow with golden sunset light, professional cinematography, 4k resolution",
    "--num-frames", "81",
    "--height", "720",
    "--width", "1280",
]

if __name__ == "__main__":
    main()
