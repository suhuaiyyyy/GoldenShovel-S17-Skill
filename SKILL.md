---
name: jcc-s17-lineup
description: Use when answering questions about 金铲铲 S17棋子、羁绊、羁绊档位、阵容筛选、装备、海克斯、经济运营或根据自然语言条件组建阵容. Includes bundled data and Python tools for fast unit/trait lookup, knowledge search, lineup building, and trait evaluation.
---

# 金铲铲 S17 阵容助手

Use this skill for 金铲铲/云顶类 S17 questions involving units, traits, trait breakpoints, items, augments, economy notes, or lineup composition.

## Data

Bundled data lives at `assets/s17_data.json` and is generated from:

- `assets/source-workbooks/金铲铲S17棋子羁绊大全.xlsx`
- `assets/source-workbooks/金铲铲S17赛季完全辅助手册_v2.xlsx`

The merged dataset includes:

- `season_overview`
- `units`
- `traits`
- `items.base_items`
- `items.completed_items`
- `items.emblems`
- `augments`
- `economy.leveling_table`
- `economy.shop_odds`
- `economy.income_rules`
- `economy.stage_guidance`
- `economy.tips`

Trait breakpoints are parsed from trait effect text:
- `(2)`, `（3）`, `(4)` style markers are treated as unlock counts.
- Text like `2未来` / `3未来` / `4未来` is also parsed for `未来战士`.
- If a trait has no explicit breakpoint text, the tools treat `1` as active so unique or descriptive traits still count.

## Tools

Run scripts from the skill directory or pass `--data assets/s17_data.json`.

```bash
python3 scripts/query_units.py 游侠
python3 scripts/query_units.py --trait 暗星 --cost 4
python3 scripts/query_traits.py 暗星
python3 scripts/query_knowledge.py 白银 --category augments
python3 scripts/query_knowledge.py 4费 --category shop_odds
python3 scripts/query_knowledge.py 蓝盾 --category completed_items
python3 scripts/build_lineup.py "在8人口下，开启羁绊数量最多的8个棋子"
python3 scripts/build_lineup.py "在7人口下，优先开启暗星和游侠"
python3 scripts/evaluate_lineup.py 贝蕾亚 雷克塞 卑尔维斯 卡莎 菲兹 泰隆 锐雯 烬
```

## Workflow

1. For unit lookup, call `query_units.py`.
2. For trait lookup and breakpoint questions, call `query_traits.py`.
3. For items, augments, season notes, leveling, D牌概率, or运营建议, call `query_knowledge.py`.
4. For lineup requests, call `build_lineup.py` with the user's original Chinese instruction.
5. For a user-provided lineup, call `evaluate_lineup.py` with unit names.
6. Summarize the returned JSON in Chinese with the fields most relevant to the user question.

## Lineup Scoring

`build_lineup.py` uses beam search plus local swaps. The default objective prioritizes:

1. number of active traits,
2. explicitly requested traits and units,
3. higher active breakpoints,
4. closeness to next breakpoints,
5. total unit cost as a final tie-breaker.

This is a deterministic recommendation helper, not a live meta-tier ranking. State that limitation when the user asks for strength, meta, or win-rate.

## Refreshing Data

If the Excel file changes:

```bash
python3 scripts/extract_data.py
```

By default, the script reads the workbooks bundled inside `assets/source-workbooks/`.
Then rerun the relevant query or lineup command.
