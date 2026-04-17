#!/usr/bin/env python3
"""
SW-1 Alpha — WAN 2.2 (5 Variant Runner)
---------------------------------------
Runs only 5 distinct variants using the existing 80s + loop pipeline logic.

Usage:
    python wan_pipeline_5_variants.py --variant ALL
    python wan_pipeline_5_variants.py --variant A
    python wan_pipeline_5_variants.py --variant D --fast
"""

import argparse
from wan_pipeline_v2 import generate_variant, VARIANT_NAMES


FIVE_VARIANTS = ["A", "C", "D", "H", "J"]


def main():
    parser = argparse.ArgumentParser(description="Run 5 WAN 2.2 SW-1 variants")
    parser.add_argument(
        "--variant",
        type=str,
        default="ALL",
        choices=FIVE_VARIANTS + ["ALL"],
        help="Choose one variant (A/C/D/H/J) or ALL",
    )
    parser.add_argument(
        "--shot",
        type=int,
        default=None,
        help="Generate only one shot number (1-16)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Use fewer inference steps for faster turnaround",
    )
    args = parser.parse_args()

    if args.variant == "ALL":
        for variant in FIVE_VARIANTS:
            print(f"\n{'=' * 60}")
            print(f"  STARTING VARIANT {variant} — {VARIANT_NAMES[variant]}")
            print(f"{'=' * 60}\n")
            generate_variant(variant, args.shot, fast=args.fast)
        print("\nDone: all 5 variants complete.")
    else:
        print(f"\n  VARIANT {args.variant} — {VARIANT_NAMES[args.variant]}\n")
        generate_variant(args.variant, args.shot, fast=args.fast)
        print(f"\nDone: variant {args.variant} complete.")


if __name__ == "__main__":
    main()
