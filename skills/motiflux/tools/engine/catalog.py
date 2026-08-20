"""The canonical machine-readable Motiflux theme catalog."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from motiflux_core import SCHEMA_VERSION, contract_errors, load_document


CATALOG_PATH = Path(__file__).resolve().parents[2] / "catalog" / "themes.json"
CATALOG_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "catalog" / "themes.schema.json"
WORD_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+", re.IGNORECASE)


def normalize_text(value: str) -> str:
    """Normalize punctuation and separators before matching theme phrases."""

    folded = value.casefold().replace("_", " ")
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", folded).strip()


@dataclass(frozen=True)
class ThemeProfile:
    id: str
    name: str
    aliases: tuple[str, ...]
    domain_tags: tuple[str, ...]
    style_tags: tuple[str, ...]
    motion_tags: tuple[str, ...]
    routing_aliases: tuple[str, ...]
    trajectory_id: str
    trajectory_summary: str
    foreground_plan: dict[str, Any]
    public_analogue: str
    design_intent: str
    algorithm_stack: tuple[str, ...]
    implementation: tuple[str, ...]
    controls: tuple[str, ...]
    exclusions: tuple[str, ...]
    qa_focus: tuple[str, ...]
    runtime: dict[str, Any]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ThemeProfile":
        routing = dict(value.get("routing", {}))
        return cls(
            id=str(value["id"]),
            name=str(value["name"]),
            aliases=tuple(str(item) for item in value.get("aliases", [])),
            domain_tags=tuple(str(item) for item in routing.get("domain_tags", [])),
            style_tags=tuple(str(item) for item in routing.get("style_tags", [])),
            motion_tags=tuple(str(item) for item in routing.get("motion_tags", [])),
            routing_aliases=tuple(str(item) for item in routing.get("aliases", [])),
            trajectory_id=str(value["trajectory_id"]),
            trajectory_summary=str(value["trajectory_summary"]),
            foreground_plan=dict(value.get("foreground_plan", {})),
            public_analogue=str(value.get("public_analogue", "")),
            design_intent=str(value["design_intent"]),
            algorithm_stack=tuple(str(item) for item in value.get("algorithm_stack", [])),
            implementation=tuple(str(item) for item in value.get("implementation", [])),
            controls=tuple(str(item) for item in value.get("controls", [])),
            exclusions=tuple(str(item) for item in value.get("exclusions", [])),
            qa_focus=tuple(str(item) for item in value.get("qa_focus", [])),
            runtime=dict(value.get("runtime", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "aliases": list(self.aliases),
            "routing": {
                "domain_tags": list(self.domain_tags),
                "style_tags": list(self.style_tags),
                "motion_tags": list(self.motion_tags),
                "aliases": list(self.routing_aliases),
            },
            "trajectory_id": self.trajectory_id,
            "trajectory_summary": self.trajectory_summary,
            "foreground_plan": self.foreground_plan,
            "public_analogue": self.public_analogue,
            "design_intent": self.design_intent,
            "algorithm_stack": list(self.algorithm_stack),
            "implementation": list(self.implementation),
            "controls": list(self.controls),
            "exclusions": list(self.exclusions),
            "qa_focus": list(self.qa_focus),
            "runtime": self.runtime,
        }


class ThemeCatalog:
    """Deep catalog interface: lookup, validate, and route theme profiles."""

    def __init__(self, profiles: tuple[ThemeProfile, ...], source_path: Path):
        self._profiles = profiles
        self.source_path = source_path
        self._by_id = {profile.id: profile for profile in profiles}
        self._by_name = {profile.name.casefold(): profile for profile in profiles}

    @property
    def profiles(self) -> tuple[ThemeProfile, ...]:
        return self._profiles

    def get(self, theme_id: str) -> ThemeProfile:
        if theme_id in self._by_name:
            return self._by_name[theme_id]
        try:
            return self._by_id[theme_id]
        except KeyError as error:
            raise ValueError(f"unknown Motiflux theme: {theme_id}") from error

    def route(self, query: str) -> dict[str, Any]:
        normalized_query = normalize_text(query)
        padded_query = f" {normalized_query} "
        query_words = {item.casefold() for item in WORD_RE.findall(normalized_query)}
        scores: dict[str, int] = {}
        matches: dict[str, list[str]] = {}
        alias_matches: dict[str, list[str]] = {}
        for profile in self._profiles:
            score = 0
            matched_tags: list[str] = []
            matched_aliases: list[str] = []
            profile_id = normalize_text(profile.id)
            profile_name = normalize_text(profile.name)
            if f" {profile_id} " in padded_query or f" {profile_name} " in padded_query:
                score += 8
                matched_tags.append(profile.name)
            for alias in dict.fromkeys((*profile.aliases, *profile.routing_aliases)):
                alias_normalized = normalize_text(alias)
                alias_words = alias_normalized.split()
                if len(alias_words) > 1 and f" {alias_normalized} " in f" {normalized_query} ":
                    score += 5
                    matched_aliases.append(alias)
                    matched_tags.append(alias)
                elif any("\u4e00" <= character <= "\u9fff" for character in alias_normalized) and alias_normalized in normalized_query:
                    score += 3
                    matched_aliases.append(alias)
                    matched_tags.append(alias)
                elif len(alias_words) == 1 and alias_normalized in query_words:
                    score += 2
                    matched_aliases.append(alias)
                    matched_tags.append(alias)
            scores[profile.id] = score
            matches[profile.id] = list(dict.fromkeys(matched_tags))
            alias_matches[profile.id] = list(dict.fromkeys(matched_aliases))

        ranked = sorted(self._profiles, key=lambda item: (-scores[item.id], item.id))
        primary = ranked[0]
        fallback = scores[primary.id] == 0
        if fallback:
            primary = self.get("system-spatial")
            modifiers = ["quiet", "accessible"]
        else:
            modifier_words = ("quiet", "bold", "technical", "organic", "playful", "cinematic", "accessible", "calm", "dramatic", "precise", "friendly", "minimal")
            modifiers = [word for word in modifier_words if word in query_words][:2]
        rejected = [profile.name for profile in ranked if profile.id != primary.id and scores[profile.id] > 0]
        return {
            "schema_version": SCHEMA_VERSION,
            "theme_selection": {
                # Keep the human-facing name on the compatibility field while
                # exposing the stable catalog ID for machine consumers.
                "primary": primary.name,
                "primary_id": primary.id,
                "primary_name": primary.name,
                "trajectory_id": primary.trajectory_id,
                "trajectory_summary": primary.trajectory_summary,
                "modifiers": modifiers,
                "matched_tags": matches[primary.id],
                "matched_aliases": alias_matches[primary.id],
                "domain_tags": list(primary.domain_tags),
                "style_tags": list(primary.style_tags),
                "motion_tags": list(primary.motion_tags),
                "rejected_candidates": rejected,
                "public_reference_basis": [primary.public_analogue] if primary.public_analogue else [],
                "algorithm_stack": list(primary.algorithm_stack),
                "implementation_controls": list(primary.controls),
                "scores": scores,
                "query": query,
                "fallback_used": fallback,
            },
        }


def load_catalog(path: Path = CATALOG_PATH) -> ThemeCatalog:
    document = load_document(path)
    schema = load_document(CATALOG_SCHEMA_PATH)
    errors = contract_errors(document, schema)
    if errors:
        raise ValueError("theme catalog contract failed: " + "; ".join(errors))
    themes = document.get("themes", [])
    profiles = tuple(ThemeProfile.from_dict(theme) for theme in themes)
    if len({profile.id for profile in profiles}) != len(profiles):
        raise ValueError("theme catalog contains duplicate IDs")
    return ThemeCatalog(profiles, path)
