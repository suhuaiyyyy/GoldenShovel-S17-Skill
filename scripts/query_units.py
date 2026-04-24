#!/usr/bin/env python3
"""Search S17 units by name, skill text, trait, or cost."""

from __future__ import annotations

import argparse
import json

from s17_core import DEFAULT_DATA, load_data, search_units


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Golden Spatula S17 units.")
    parser.add_argument("query", nargs="?", default="", help="Keyword in unit name, skill, description, or traits.")
    parser.add_argument("--trait", help="Only return units with this trait.")
    parser.add_argument("--cost", type=int, choices=[1, 2, 3, 4, 5], help="Only return units with this cost.")
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="Path to s17_data.json.")
    parser.add_argument("--names-only", action="store_true", help="Print only unit names.")
    args = parser.parse_args()

    data = load_data(args.data)
    results = search_units(data, query=args.query, trait=args.trait, cost=args.cost)
    if args.names_only:
        print("\n".join(unit["name"] for unit in results))
        return
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
