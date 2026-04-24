#!/usr/bin/env python3
"""Evaluate explicit S17 units and print active trait progress."""

from __future__ import annotations

import argparse
import json

from s17_core import DEFAULT_DATA, Preferences, compact_lineup_result, evaluate_lineup, load_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a Golden Spatula S17 lineup.")
    parser.add_argument("units", nargs="+", help="Unit names in the lineup.")
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="Path to s17_data.json.")
    args = parser.parse_args()

    data = load_data(args.data)
    by_name = {unit["name"]: unit for unit in data["units"]}
    missing = [name for name in args.units if name not in by_name]
    lineup = [by_name[name] for name in args.units if name in by_name]
    result = {"lineup": lineup, "evaluation": evaluate_lineup(lineup, data, Preferences(level=len(lineup)))}
    output = compact_lineup_result(result)
    if missing:
        output["missing_units"] = missing
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
