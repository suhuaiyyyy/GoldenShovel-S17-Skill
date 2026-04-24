#!/usr/bin/env python3
"""Extract S17 roster and manual data into assets/s17_data.json."""

from __future__ import annotations

import argparse
import json

from s17_core import DEFAULT_DATA, DEFAULT_MANUAL_XLSX, DEFAULT_ROSTER_XLSX, extract_data, save_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Golden Spatula S17 data from workbook(s).")
    parser.add_argument("--roster-xlsx", default=str(DEFAULT_ROSTER_XLSX), help="Path to 金铲铲S17棋子羁绊大全.xlsx")
    parser.add_argument("--manual-xlsx", default=str(DEFAULT_MANUAL_XLSX), help="Path to 金铲铲S17赛季完全辅助手册.xlsx")
    parser.add_argument("--out", default=str(DEFAULT_DATA), help="Output JSON path.")
    args = parser.parse_args()

    data = extract_data(roster_xlsx=args.roster_xlsx, manual_xlsx=args.manual_xlsx)
    save_data(data, args.out)
    print(
        json.dumps(
            {
                "output": args.out,
                "sources": data["sources"],
                "overview_topics": len(data["season_overview"]),
                "units": len(data["units"]),
                "traits": len(data["traits"]),
                "base_items": len(data["items"]["base_items"]),
                "completed_items": len(data["items"]["completed_items"]),
                "emblems": len(data["items"]["emblems"]),
                "augments": len(data["augments"]),
                "economy_rows": sum(len(rows) for rows in data["economy"].values()),
                "tiers": sum(len(trait["tiers"]) for trait in data["traits"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
