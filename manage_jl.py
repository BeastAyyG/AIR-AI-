import sys
import os

os.environ["JL_API_KEY"] = "mgMHYQlRZqsDXo988uk1Ux4uzRxTeXAxScvRNU3QTgA"

from jarvislabs.cli.app import main

sys.argv[0] = "jl"

if __name__ == "__main__":
    main()
