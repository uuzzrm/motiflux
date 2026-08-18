"""Route a request to one Motiflux theme and a small algorithm stack."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from motiflux_core import SCHEMA_VERSION, write_json


GUIDE_PATH = Path(__file__).resolve().parents[1] / "guides" / "motion-themes.md"
THEME_HEADING = re.compile(r"^##\s+\d+\.\s+(.+?)\s*$", re.MULTILINE)
WORD_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+", re.IGNORECASE)
MODIFIERS = (
    "quiet",
    "bold",
    "technical",
    "organic",
    "playful",
    "cinematic",
    "accessible",
    "calm",
    "dramatic",
    "structured",
    "clear",
    "precise",
    "friendly",
    "minimal",
)
ALIASES = {
    "material": "System-spatial",
    "google material": "System-spatial",
    "apple hig": "Premium-quiet",
    "fluent": "System-spatial",
    "adobe spectrum": "System-spatial",
    "atlassian": "Developer-open",
    "shopify polaris": "Commerce-energy",
    "github primer": "Developer-open",
    "airbnb lottie": "Developer-open",
    "科技": "System-spatial",
    "产品": "System-spatial",
    "企业系统": "System-spatial",
    "奢侈": "Premium-quiet",
    "时尚": "Premium-quiet",
    "美妆": "Premium-quiet",
    "开发者": "Developer-open",
    "开源": "Developer-open",
    "代码": "Developer-open",
    "人工智能": "AI-field",
    "生成式": "AI-field",
    "金融": "Fintech-trust",
    "支付": "Fintech-trust",
    "银行": "Fintech-trust",
    "安全": "Security-shield",
    "隐私": "Security-shield",
    "认证": "Security-shield",
    "电商": "Commerce-energy",
    "零售": "Commerce-energy",
    "汽车": "Automotive-precision",
    "交通": "Automotive-precision",
    "体育": "Sports-impact",
    "健身": "Sports-impact",
    "电影": "Cinematic-title",
    "片头": "Cinematic-title",
    "自然": "Nature-flow",
    "有机": "Nature-flow",
    "游戏": "Gaming-world",
    "电竞": "Gaming-world",
    "无障碍": "Accessibility-first",
    "低动效": "Accessibility-first",
}


def words(value: str) -> set[str]:
    return {item.casefold() for item in WORD_RE.findall(value)}


def parse_themes(markdown: str) -> list[dict[str, Any]]:
    headings = list(THEME_HEADING.finditer(markdown))
    themes: list[dict[str, Any]] = []
    for index, heading in enumerate(headings):
        # Composition is guidance for combining real themes, not a routable
        # theme of its own.
        if heading.group(1).strip().casefold() == "theme composition":
            continue
        block_end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
        block = markdown[heading.end():block_end]
        tag_match = re.search(r"^Tags:\s*(.+)$", block, re.MULTILINE)
        analogue_match = re.search(r"^Public analogues:\s*(.+)$", block, re.MULTILINE)
        algorithm_match = re.search(
            r"^Algorithm stack:\s*(.*?)(?=^Implementation:|^Design intent:|^Controls:|^Exclude:|^QA focus:|\Z)",
            block,
            re.MULTILINE | re.DOTALL,
        )
        algorithms = []
        if algorithm_match:
            algorithms = [
                line.strip()[2:].strip()
                for line in algorithm_match.group(1).splitlines()
                if line.strip().startswith("-")
            ]
        themes.append(
            {
                "name": heading.group(1).strip(),
                "tags": [tag.strip() for tag in (tag_match.group(1).split(",") if tag_match else [])],
                "analogue": analogue_match.group(1).strip() if analogue_match else "",
                "algorithms": algorithms,
            }
        )
    return themes


def route(query: str, guide_path: Path = GUIDE_PATH) -> dict[str, Any]:
    themes = parse_themes(guide_path.read_text(encoding="utf-8"))
    if not themes:
        raise ValueError("motion theme guide contains no numbered theme records")
    query_folded = query.casefold()
    query_words = words(query)
    scores: dict[str, int] = {}
    matched_by_theme: dict[str, list[str]] = {}
    for theme in themes:
        score = 0
        matched: list[str] = []
        name_folded = theme["name"].casefold()
        if name_folded in query_folded:
            score += 8
            matched.append(theme["name"])
        for tag in theme["tags"]:
            tag_folded = tag.casefold()
            if tag_folded in query_folded:
                score += 3
                matched.append(tag)
            elif tag_folded in query_words:
                score += 2
                matched.append(tag)
        for alias, target in ALIASES.items():
            if target.casefold() == name_folded and alias.casefold() in query_folded:
                score += 5
                matched.append(alias)
        scores[theme["name"]] = score
        matched_by_theme[theme["name"]] = list(dict.fromkeys(matched))

    ranked = sorted(themes, key=lambda item: (-scores[item["name"]], item["name"]))
    primary = ranked[0]
    if scores[primary["name"]] == 0:
        primary = next((item for item in themes if item["name"] == "System-spatial"), themes[0])
        modifiers = ["quiet", "accessible"]
        fallback = True
    else:
        explicit_modifiers = [modifier for modifier in MODIFIERS if modifier in query_words]
        modifiers = explicit_modifiers[:2]
        fallback = False
    rejected = [
        item["name"]
        for item in ranked
        if item["name"] != primary["name"] and scores[item["name"]] > 0
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "theme_selection": {
            "primary": primary["name"],
            "modifiers": modifiers,
            "matched_tags": matched_by_theme[primary["name"]],
            "rejected_candidates": rejected,
            "public_reference_basis": [primary["analogue"]] if primary["analogue"] else [],
            "algorithm_stack": primary["algorithms"],
            "scores": scores,
            "query": query,
            "fallback_used": fallback,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    write_json(args.output, route(args.query))


if __name__ == "__main__":
    main()
