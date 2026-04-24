#!/usr/bin/env python3
"""Search S17 traits and show parsed breakpoints."""

from __future__ import annotations

import argparse
import json

from s17_core import DEFAULT_DATA, load_data, search_traits


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Golden Spatula S17 traits.")
    parser.add_argument("query", nargs="?", default="", help="Keyword in trait name, effect, or included units.")
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="Path to s17_data.json.")
    parser.add_argument("--names-only", action="store_true", help="Print only trait names.")
    args = parser.parse_args()

    data = load_data(args.data)
    results = search_traits(data, args.query)
    if args.names_only:
        print("\n".join(trait["name"] for trait in results))
        return
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
