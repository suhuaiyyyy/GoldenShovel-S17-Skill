#!/usr/bin/env python3
"""Core utilities for Golden Spatula S17 data extraction and lineup queries."""

from __future__ import annotations

import itertools
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zipfile import ZipFile


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_DATA = SKILL_DIR / "assets" / "s17_data.json"
DEFAULT_ROSTER_XLSX = SKILL_DIR / "assets" / "source-workbooks" / "金铲铲S17棋子羁绊大全.xlsx"
DEFAULT_MANUAL_XLSX = SKILL_DIR / "assets" / "source-workbooks" / "金铲铲S17赛季完全辅助手册.xlsx"

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def split_cn_list(value: str) -> list[str]:
    return [x.strip() for x in re.split(r"[、,，]", value or "") if x.strip()]


def col_to_idx(ref: str) -> int:
    letters = "".join(ch for ch in ref if ch.isalpha())
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch.upper()) - 64
    return n - 1


def cell_text(cell: ET.Element) -> str:
    if cell.attrib.get("t") == "inlineStr":
        return "".join(t.text or "" for t in cell.findall(".//m:t", NS)).strip()
    value = cell.find("m:v", NS)
    return (value.text if value is not None else "").strip()


def read_sheet(xlsx_path: str | Path, sheet_name: str) -> list[list[str]]:
    with ZipFile(xlsx_path) as archive:
        root = ET.fromstring(archive.read(f"xl/worksheets/{sheet_name}"))
    rows: list[list[str]] = []
    for row in root.findall(".//m:row", NS):
        values: dict[int, str] = {}
        for cell in row.findall("m:c", NS):
            values[col_to_idx(cell.attrib["r"])] = cell_text(cell)
        if values:
            rows.append([values.get(i, "") for i in range(max(values) + 1)])
    return rows


def parse_tiers(effect: str, trait_name: str, unit_count: int) -> tuple[list[int], bool]:
    found: set[int] = set()
    for match in re.finditer(r"[\(（]\s*(\d+)\s*[\)）]", effect or ""):
        found.add(int(match.group(1)))

    escaped_name = re.escape(trait_name)
    direct_pattern = re.compile(rf"(?:^|[^0-9])(\d+)\s*{escaped_name}")
    for match in direct_pattern.finditer(effect or ""):
        found.add(int(match.group(1)))

    if trait_name == "未来战士":
        for match in re.finditer(r"(?:^|[^0-9])([234])\s*未来", effect or ""):
            found.add(int(match.group(1)))

    explicit = bool(found)
    if not found:
        found.add(1)
    return sorted(x for x in found if x > 0), explicit


def empty_dataset() -> dict[str, Any]:
    return {
        "sources": [],
        "season_overview": [],
        "units": [],
        "traits": [],
        "items": {"base_items": [], "completed_items": [], "emblems": []},
        "augments": [],
        "economy": {
            "leveling_table": [],
            "shop_odds": [],
            "income_rules": [],
            "stage_guidance": [],
            "tips": [],
        },
    }


def extract_roster_xlsx(xlsx_path: str | Path, units_sheet: str = "sheet1.xml", traits_sheet: str = "sheet2.xml") -> dict[str, Any]:
    units_rows = read_sheet(xlsx_path, units_sheet)
    traits_rows = read_sheet(xlsx_path, traits_sheet)
    data = empty_dataset()
    data["sources"].append({"path": str(xlsx_path), "kind": "roster"})

    for row in units_rows[1:]:
        row = row + [""] * 5
        name, cost, skill, description, traits = row[:5]
        if not name:
            continue
        data["units"].append(
            {
                "name": name,
                "cost": int(float(cost)) if cost else 0,
                "skill": skill,
                "description": description,
                "traits": split_cn_list(traits),
            }
        )

    for row in traits_rows[1:]:
        row = row + [""] * 4
        name, effect, unit_count, champions = row[:4]
        if not name:
            continue
        count = int(float(unit_count)) if unit_count else 0
        tiers, explicit = parse_tiers(effect, name, count)
        data["traits"].append(
            {
                "name": name,
                "type": "",
                "effect": effect,
                "unit_count": count,
                "champions": split_cn_list(champions),
                "tiers": tiers,
                "explicit_tiers": explicit,
            }
        )
    return data


def extract_manual_xlsx(xlsx_path: str | Path) -> dict[str, Any]:
    overview_rows = read_sheet(xlsx_path, "sheet1.xml")
    units_rows = read_sheet(xlsx_path, "sheet2.xml")
    traits_rows = read_sheet(xlsx_path, "sheet3.xml")
    items_rows = read_sheet(xlsx_path, "sheet4.xml")
    augments_rows = read_sheet(xlsx_path, "sheet5.xml")
    economy_rows = read_sheet(xlsx_path, "sheet6.xml")

    data = empty_dataset()
    data["sources"].append({"path": str(xlsx_path), "kind": "manual"})

    for row in overview_rows[2:]:
        row = row + [""] * 2
        key, value = row[:2]
        if key and value:
            data["season_overview"].append({"topic": key, "content": value})

    for row in units_rows[1:]:
        row = row + [""] * 5
        name, cost, skill, description, traits = row[:5]
        if not name:
            continue
        data["units"].append(
            {
                "name": name,
                "cost": int(float(cost)) if cost else 0,
                "skill": skill,
                "description": description,
                "traits": split_cn_list(traits),
            }
        )

    for row in traits_rows[1:]:
        row = row + [""] * 5
        name, trait_type, effect, unit_count, champions = row[:5]
        if not name:
            continue
        count = int(float(unit_count)) if unit_count else 0
        tiers, explicit = parse_tiers(effect, name, count)
        data["traits"].append(
            {
                "name": name,
                "type": trait_type,
                "effect": effect,
                "unit_count": count,
                "champions": split_cn_list(champions),
                "tiers": tiers,
                "explicit_tiers": explicit,
            }
        )

    item_section = ""
    for row in items_rows:
        row = row + [""] * 4
        first = row[0].strip() if row else ""
        if first == "基础散件":
            item_section = "base_items"
            continue
        if first == "成装名称":
            item_section = "completed_items"
            continue
        if first == "转职纹章":
            item_section = "emblems"
            continue
        if not any(cell.strip() for cell in row):
            continue
        if item_section == "base_items" and len(row) >= 3:
            data["items"]["base_items"].append(
                {"name": row[0], "icon": row[1], "feature": row[2]}
            )
        elif item_section == "completed_items" and len(row) >= 4:
            data["items"]["completed_items"].append(
                {"name": row[0], "recipe": row[1], "effect": row[2], "usage": row[3]}
            )
        elif item_section == "emblems" and len(row) >= 3:
            data["items"]["emblems"].append(
                {"name": row[0], "recipe": row[1], "description": row[2]}
            )

    for row in augments_rows[1:]:
        row = row + [""] * 3
        level, name, effect = row[:3]
        if name:
            data["augments"].append({"level": level, "name": name, "effect": effect})

    eco_section = ""
    for row in economy_rows:
        row = row + [""] * 6
        first = row[0].strip() if row else ""
        if first.startswith("一、"):
            eco_section = "leveling_table"
            continue
        if first.startswith("二、"):
            eco_section = "shop_odds"
            continue
        if first.startswith("三、"):
            eco_section = "income_rules"
            continue
        if first.startswith("四、"):
            eco_section = "stage_guidance"
            continue
        if first.startswith("五、"):
            eco_section = "tips"
            continue
        if not any(cell.strip() for cell in row):
            continue
        if eco_section == "leveling_table" and first != "人口等级":
            data["economy"]["leveling_table"].append(
                {"level": row[0], "xp": row[1], "gold": row[2]}
            )
        elif eco_section == "shop_odds" and first != "人口等级":
            data["economy"]["shop_odds"].append(
                {"level": row[0], "1_cost": row[1], "2_cost": row[2], "3_cost": row[3], "4_cost": row[4], "5_cost": row[5]}
            )
        elif eco_section == "income_rules":
            data["economy"]["income_rules"].append(
                {"topic": row[0], "rule": row[1], "note": row[2]}
            )
        elif eco_section == "stage_guidance" and first != "阶段":
            data["economy"]["stage_guidance"].append(
                {"stage": row[0], "recommended_level": row[1], "goal": row[2]}
            )
        elif eco_section == "tips":
            data["economy"]["tips"].append(
                {"topic": row[0], "advice": row[1], "note": row[2]}
            )

    return data


def dedupe_by_name(entries: list[dict[str, Any]], key: str = "name") -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for entry in entries:
        entry_key = entry.get(key)
        if not entry_key:
            continue
        if entry_key in merged:
            merged[entry_key] = {**merged[entry_key], **entry}
        else:
            merged[entry_key] = dict(entry)
    return sorted(merged.values(), key=lambda x: str(x.get(key, "")))


def merge_data(*datasets: dict[str, Any]) -> dict[str, Any]:
    merged = empty_dataset()
    for data in datasets:
        if not data:
            continue
        merged["sources"].extend(data.get("sources", []))
        merged["season_overview"].extend(data.get("season_overview", []))
        merged["units"].extend(data.get("units", []))
        merged["traits"].extend(data.get("traits", []))
        items = data.get("items", {})
        merged["items"]["base_items"].extend(items.get("base_items", []))
        merged["items"]["completed_items"].extend(items.get("completed_items", []))
        merged["items"]["emblems"].extend(items.get("emblems", []))
        merged["augments"].extend(data.get("augments", []))
        economy = data.get("economy", {})
        for key in merged["economy"]:
            merged["economy"][key].extend(economy.get(key, []))

    merged["season_overview"] = dedupe_by_name(
        [{"name": row["topic"], **row} for row in merged["season_overview"]],
        key="name",
    )
    merged["season_overview"] = [
        {"topic": row["topic"], "content": row["content"]} for row in merged["season_overview"]
    ]
    merged["units"] = dedupe_by_name(merged["units"])
    merged["traits"] = dedupe_by_name(merged["traits"])
    merged["items"]["base_items"] = dedupe_by_name(merged["items"]["base_items"])
    merged["items"]["completed_items"] = dedupe_by_name(merged["items"]["completed_items"])
    merged["items"]["emblems"] = dedupe_by_name(merged["items"]["emblems"])
    merged["augments"] = dedupe_by_name(merged["augments"])
    return merged


def extract_data(roster_xlsx: str | Path | None = None, manual_xlsx: str | Path | None = None) -> dict[str, Any]:
    datasets: list[dict[str, Any]] = []
    if roster_xlsx:
        datasets.append(extract_roster_xlsx(roster_xlsx))
    if manual_xlsx:
        datasets.append(extract_manual_xlsx(manual_xlsx))
    if not datasets:
        raise ValueError("At least one xlsx source is required.")
    return merge_data(*datasets)


def load_data(path: str | Path | None = None) -> dict[str, Any]:
    data_path = Path(path) if path else DEFAULT_DATA
    with data_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_data(data: dict[str, Any], path: str | Path | None = None) -> None:
    data_path = Path(path) if path else DEFAULT_DATA
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


@dataclass(frozen=True)
class Preferences:
    level: int = 8
    traits: tuple[str, ...] = ()
    units: tuple[str, ...] = ()
    max_cost: int | None = None
    exact_cost: int | None = None


def parse_prompt(prompt: str, data: dict[str, Any], fallback_level: int = 8) -> Preferences:
    level_match = re.search(r"(\d+)\s*(?:人口|人|个棋子|枚棋子|位)", prompt or "")
    level = int(level_match.group(1)) if level_match else fallback_level
    level = max(1, min(10, level))

    wanted_traits = tuple(t["name"] for t in data["traits"] if t["name"] in prompt)
    wanted_units = tuple(u["name"] for u in data["units"] if u["name"] in prompt)

    max_cost_match = re.search(r"(?:不超过|最多|最高)\s*(\d)\s*费", prompt or "")
    exact_cost_match = re.search(r"(\d)\s*费", prompt or "")
    max_cost = int(max_cost_match.group(1)) if max_cost_match else None
    exact_cost = int(exact_cost_match.group(1)) if exact_cost_match and not max_cost else None

    return Preferences(level=level, traits=wanted_traits, units=wanted_units, max_cost=max_cost, exact_cost=exact_cost)


def count_traits(lineup: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for unit in lineup:
        for trait in unit.get("traits", []):
            counts[trait] = counts.get(trait, 0) + 1
    return counts


def evaluate_lineup(lineup: list[dict[str, Any]], data: dict[str, Any], preferences: Preferences | None = None) -> dict[str, Any]:
    preferences = preferences or Preferences(level=len(lineup))
    counts = count_traits(lineup)
    details: list[dict[str, Any]] = []
    for trait in data["traits"]:
        count = counts.get(trait["name"], 0)
        tiers = trait.get("tiers") or [1]
        active_tiers = [tier for tier in tiers if count >= tier]
        active_tier = active_tiers[-1] if active_tiers else 0
        next_tier = next((tier for tier in tiers if count < tier), 0)
        if count > 0 or active_tier:
            details.append(
                {
                    "name": trait["name"],
                    "count": count,
                    "tiers": tiers,
                    "active": active_tier > 0,
                    "active_tier": active_tier,
                    "next_tier": next_tier,
                    "explicit_tiers": trait.get("explicit_tiers", False),
                    "effect": trait.get("effect", ""),
                    "type": trait.get("type", ""),
                }
            )

    active = [item for item in details if item["active"]]
    tier_score = sum(item["active_tier"] for item in active)
    near_score = sum(max(0, 4 - (item["next_tier"] - item["count"])) for item in details if item["next_tier"])
    trait_density = len({trait for unit in lineup for trait in unit.get("traits", [])})
    cost_score = sum(unit.get("cost", 0) for unit in lineup)
    preference_score = 0
    for trait_name in preferences.traits:
        detail = next((item for item in details if item["name"] == trait_name), None)
        if detail:
            preference_score += 2200
            if detail["active"]:
                preference_score += 14000
    for unit_name in preferences.units:
        if any(unit["name"] == unit_name for unit in lineup):
            preference_score += 8000

    score = len(active) * 10000 + preference_score + tier_score * 110 + near_score * 18 + trait_density * 6 + cost_score
    return {
        "score": score,
        "unit_count": len(lineup),
        "total_cost": cost_score,
        "active_trait_count": len(active),
        "tier_score": tier_score,
        "near_score": near_score,
        "traits": sorted(details, key=lambda x: (not x["active"], -x["count"], x["name"])),
    }


def candidate_units(data: dict[str, Any], preferences: Preferences) -> list[dict[str, Any]]:
    units = list(data["units"])
    if preferences.max_cost:
        units = [unit for unit in units if unit["cost"] <= preferences.max_cost]
    if preferences.exact_cost:
        units = [unit for unit in units if unit["cost"] == preferences.exact_cost]

    def sort_key(unit: dict[str, Any]) -> tuple[int, int, int, str]:
        preferred = unit["name"] in preferences.units or any(trait in preferences.traits for trait in unit.get("traits", []))
        return (int(preferred), len(unit.get("traits", [])), unit["cost"], unit["name"])

    return sorted(units, key=sort_key, reverse=True)


def state_key(lineup: list[dict[str, Any]]) -> tuple[str, ...]:
    return tuple(sorted(unit["name"] for unit in lineup))


def build_lineup(data: dict[str, Any], preferences: Preferences, beam_width: int | None = None) -> dict[str, Any]:
    target = min(preferences.level, len(data["units"]))
    candidates = candidate_units(data, preferences)
    if not candidates:
        return {"lineup": [], "evaluation": evaluate_lineup([], data, preferences)}

    beam_width = beam_width or (1600 if target >= 9 else 2200)
    beam: list[list[dict[str, Any]]] = [[]]

    for _ in range(target):
        next_states: list[list[dict[str, Any]]] = []
        seen: set[tuple[str, ...]] = set()
        for lineup in beam:
            used = {unit["name"] for unit in lineup}
            for unit in candidates:
                if unit["name"] in used:
                    continue
                candidate = lineup + [unit]
                key = state_key(candidate)
                if key in seen:
                    continue
                seen.add(key)
                next_states.append(candidate)
        next_states.sort(key=lambda x: evaluate_lineup(x, data, preferences)["score"], reverse=True)
        beam = next_states[:beam_width]

    best = beam[0] if beam else candidates[:target]
    best_score = evaluate_lineup(best, data, preferences)["score"]
    improved = True
    while improved:
        improved = False
        used = {unit["name"] for unit in best}
        for index, _ in enumerate(best):
            for unit in candidates:
                if unit["name"] in used:
                    continue
                next_lineup = list(best)
                next_lineup[index] = unit
                score = evaluate_lineup(next_lineup, data, preferences)["score"]
                if score > best_score:
                    best = next_lineup
                    best_score = score
                    improved = True
                    break
            if improved:
                break

    best = sorted(best, key=lambda unit: (unit["cost"], unit["name"]))
    return {"lineup": best, "evaluation": evaluate_lineup(best, data, preferences)}


def search_units(data: dict[str, Any], query: str = "", trait: str | None = None, cost: int | None = None) -> list[dict[str, Any]]:
    query = (query or "").lower()
    results = []
    for unit in data["units"]:
        text = " ".join([unit["name"], unit.get("skill", ""), unit.get("description", ""), " ".join(unit.get("traits", []))]).lower()
        if query and query not in text:
            continue
        if trait and trait not in unit.get("traits", []):
            continue
        if cost and unit.get("cost") != cost:
            continue
        results.append(unit)
    return results


def search_traits(data: dict[str, Any], query: str = "") -> list[dict[str, Any]]:
    query = (query or "").lower()
    results = []
    for trait in data["traits"]:
        text = " ".join([trait["name"], trait.get("type", ""), trait.get("effect", ""), " ".join(trait.get("champions", []))]).lower()
        if not query or query in text:
            results.append(trait)
    return results


def search_knowledge(data: dict[str, Any], query: str = "", category: str | None = None) -> list[dict[str, Any]]:
    query = (query or "").lower()
    categories = {
        "overview": [{"category": "overview", **row} for row in data.get("season_overview", [])],
        "base_items": [{"category": "base_items", **row} for row in data.get("items", {}).get("base_items", [])],
        "completed_items": [{"category": "completed_items", **row} for row in data.get("items", {}).get("completed_items", [])],
        "emblems": [{"category": "emblems", **row} for row in data.get("items", {}).get("emblems", [])],
        "augments": [{"category": "augments", **row} for row in data.get("augments", [])],
        "leveling_table": [{"category": "leveling_table", **row} for row in data.get("economy", {}).get("leveling_table", [])],
        "shop_odds": [{"category": "shop_odds", **row} for row in data.get("economy", {}).get("shop_odds", [])],
        "income_rules": [{"category": "income_rules", **row} for row in data.get("economy", {}).get("income_rules", [])],
        "stage_guidance": [{"category": "stage_guidance", **row} for row in data.get("economy", {}).get("stage_guidance", [])],
        "tips": [{"category": "tips", **row} for row in data.get("economy", {}).get("tips", [])],
    }
    selected = categories.keys() if not category else [category]
    results: list[dict[str, Any]] = []
    for key in selected:
        for row in categories.get(key, []):
            text = " ".join(str(value) for value in row.values()).lower()
            if not query or query in text:
                results.append(row)
    return results


def compact_lineup_result(result: dict[str, Any]) -> dict[str, Any]:
    evaluation = result["evaluation"]
    return {
        "units": [
            {"name": unit["name"], "cost": unit["cost"], "traits": unit.get("traits", [])}
            for unit in result["lineup"]
        ],
        "summary": {
            "unit_count": evaluation["unit_count"],
            "total_cost": evaluation["total_cost"],
            "active_trait_count": evaluation["active_trait_count"],
            "tier_score": evaluation["tier_score"],
            "score": evaluation["score"],
        },
        "active_traits": [
            item for item in evaluation["traits"] if item["active"]
        ],
        "inactive_progress": [
            item for item in evaluation["traits"] if not item["active"]
        ],
    }


def combinations_baseline(data: dict[str, Any], preferences: Preferences, limit: int = 5) -> list[dict[str, Any]]:
    candidates = candidate_units(data, preferences)
    if preferences.level > 6 or len(candidates) > 35:
        return []
    ranked = []
    for lineup in itertools.combinations(candidates, preferences.level):
        result = {"lineup": list(lineup), "evaluation": evaluate_lineup(list(lineup), data, preferences)}
        ranked.append(result)
    ranked.sort(key=lambda x: x["evaluation"]["score"], reverse=True)
    return [compact_lineup_result(item) for item in ranked[:limit]]
