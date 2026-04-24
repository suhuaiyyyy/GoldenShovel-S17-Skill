#!/usr/bin/env python3
"""Search S17 season overview, items, augments, and economy notes."""

from __future__ import annotations

import argparse
import json

from s17_core import DEFAULT_DATA, load_data, search_knowledge


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Golden Spatula S17 reference knowledge.")
    parser.add_argument("query", nargs="?", default="", help="Keyword in overview, items, augments, or economy notes.")
    parser.add_argument(
        "--category",
        choices=[
            "overview",
            "base_items",
            "completed_items",
            "emblems",
            "augments",
            "leveling_table",
            "shop_odds",
            "income_rules",
            "stage_guidance",
            "tips",
        ],
        help="Limit search to one knowledge category.",
    )
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="Path to s17_data.json.")
    parser.add_argument("--names-only", action="store_true", help="Print only the main name/topic field.")
    args = parser.parse_args()

    data = load_data(args.data)
    results = search_knowledge(data, query=args.query, category=args.category)
    if args.names_only:
        keys = []
        for row in results:
            keys.append(
                row.get("name")
                or row.get("topic")
                or row.get("stage")
                or row.get("level")
                or row.get("category", "")
            )
        print("\n".join(str(x) for x in keys if x))
        return
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
