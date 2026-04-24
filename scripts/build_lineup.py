#!/usr/bin/env python3
"""Build a S17 lineup from a natural-language request."""

from __future__ import annotations

import argparse
import json

from s17_core import DEFAULT_DATA, Preferences, build_lineup, compact_lineup_result, load_data, parse_prompt


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Golden Spatula S17 lineups.")
    parser.add_argument("prompt", nargs="?", default="在8人口下，开启羁绊数量最多的8个棋子")
    parser.add_argument("--level", type=int, default=8, help="Fallback population if prompt has no level.")
    parser.add_argument("--trait", action="append", default=[], help="Preferred trait. Can be repeated.")
    parser.add_argument("--unit", action="append", default=[], help="Required/preferred unit. Can be repeated.")
    parser.add_argument("--max-cost", type=int, choices=[1, 2, 3, 4, 5], help="Maximum unit cost.")
    parser.add_argument("--exact-cost", type=int, choices=[1, 2, 3, 4, 5], help="Exact unit cost.")
    parser.add_argument("--beam-width", type=int, help="Beam search width.")
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="Path to s17_data.json.")
    parser.add_argument("--full", action="store_true", help="Output full skill/effect details.")
    args = parser.parse_args()

    data = load_data(args.data)
    parsed = parse_prompt(args.prompt, data, fallback_level=args.level)
    preferences = Preferences(
        level=parsed.level,
        traits=tuple(dict.fromkeys([*parsed.traits, *args.trait])),
        units=tuple(dict.fromkeys([*parsed.units, *args.unit])),
        max_cost=args.max_cost if args.max_cost else parsed.max_cost,
        exact_cost=args.exact_cost if args.exact_cost else parsed.exact_cost,
    )
    result = build_lineup(data, preferences, beam_width=args.beam_width)
    output = result if args.full else compact_lineup_result(result)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
