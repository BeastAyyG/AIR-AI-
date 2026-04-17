import sys
import os

os.environ["JL_API_KEY"] = "Z9TRPZhaPtlT1Ptd9m6f6pjKGIkWivG741tmc4aFHnw"

from jarvislabs.cli.app import main
sys.argv = [
    "jl", "run", "logs", "r_df1463ce"
]

if __name__ == "__main__":
    main()
