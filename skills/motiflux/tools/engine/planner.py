"""Create a contract-valid motion plan from source observations and a theme."""

from __future__ import annotations

from typing import Any

from .catalog import ThemeProfile


def build_plan(source_analysis: dict[str, Any], selection: dict[str, Any], profile: ThemeProfile, *, project_name: str, source_name: str) -> dict[str, Any]:
    records = source_analysis.get("observations", {}).get("elements", [])
    actor_ids = [str(item.get("id")) for item in records if isinstance(item, dict) and item.get("id")]
    if not actor_ids:
        actor_ids = ["mark"]
    beat_defs = [
        {"id": "orient", "intent": "establish the source mark and motion direction", "duration_weight": 1},
        {"id": "form", "intent": f"apply the {profile.id} motion language to identity-bearing actors", "duration_weight": 2},
        {"id": "resolve", "intent": "settle into the canonical mark without changing identity", "duration_weight": 1},
    ]
    actors = [
        {
            "id": actor_id,
            "role": "identity-bearing actor" if index == 0 else "secondary source actor",
            "geometry_strategy": "preserve-source-vector",
            "parent": None,
            "anchor": "source-bounds",
            "layer": index,
            "occludes": [],
            "occluded_by": [],
        }
        for index, actor_id in enumerate(actor_ids)
    ]
    dependencies = [
        {
            "actor": actor_id,
            "beat": "form",
            "starts_after": ["orient"],
            "may_overlap": [],
            "must_finish_before": ["resolve"],
            "anchor": "source-bounds",
            "property_channels": ["opacity", "transform", "secondary-effect"],
        }
        for actor_id in actor_ids
    ]
    return {
        "schema_version": "1.0",
        "project": {"name": project_name, "surface": "responsive web intro", "source": source_name},
        "theme_selection": {
            **selection["theme_selection"],
            "catalog_id": "motiflux-motion-themes",
            "primary_id": profile.id,
        },
        "motion_language": {
            "traits": [
                {"name": "tempo", "value": profile.runtime.get("tempo", 1.0), "trace": profile.algorithm_stack[0]},
                {"name": "settle", "value": profile.runtime.get("settle_damping", 0.82), "trace": "canonical end-state requirement"},
                {"name": "secondary-effect", "value": profile.runtime.get("secondary_effect", "plain"), "trace": profile.algorithm_stack[-1]},
            ],
            "design_intent": profile.design_intent,
            "implementation_controls": list(profile.controls),
        },
        "constraints": [
            {"id": "identity-source", "kind": "topology", "importance": "identity", "target": "preserve source actor IDs and canonical paint", "tolerance": 0},
            {"id": "canonical-end-state", "kind": "landmark", "importance": "identity", "target": "exact source vector fingerprint after finish", "tolerance": 0},
        ],
        "actors": actors,
        "beats": beat_defs,
        "dependencies": dependencies,
        "runtime": {
            "duration_ms": 1400,
            "reduced_motion": "static-canonical",
            "seed": 0,
            "tempo": profile.runtime.get("tempo", 1.0),
            "settle_damping": profile.runtime.get("settle_damping", 0.82),
            "secondary_effect": profile.runtime.get("secondary_effect", "plain"),
            "controls": ["play", "pause", "replay", "tempo"],
        },
    }


def validate_references(
    plan: dict[str, Any],
    *,
    theme_ids: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    beat_ids = {str(beat.get("id")) for beat in plan.get("beats", []) if isinstance(beat, dict)}
    actor_ids = {str(actor.get("id")) for actor in plan.get("actors", []) if isinstance(actor, dict)}
    beat_records = [beat for beat in plan.get("beats", []) if isinstance(beat, dict)]
    actor_records = [actor for actor in plan.get("actors", []) if isinstance(actor, dict)]
    if len(beat_ids) != len(beat_records):
        errors.append("beats contain duplicate IDs")
    if len(actor_ids) != len(actor_records):
        errors.append("actors contain duplicate IDs")

    theme_selection = plan.get("theme_selection", {})
    theme = theme_selection.get("primary")
    theme_id = theme_selection.get("primary_id")
    if not theme and not theme_id:
        errors.append("theme_selection.primary or primary_id is required")
    if theme_ids is not None and theme_id not in theme_ids:
        errors.append(f"theme_selection references unknown theme: {theme_id}")

    for actor in actor_records:
        parent = actor.get("parent")
        if parent is not None and parent not in actor_ids:
            errors.append(f"actor references unknown parent: {parent}")
        for key in ("occludes", "occluded_by"):
            for actor_id in actor.get(key, []) or []:
                if actor_id not in actor_ids:
                    errors.append(f"actor {key} references unknown actor: {actor_id}")

    for dependency in plan.get("dependencies", []):
        if not isinstance(dependency, dict):
            errors.append("dependencies must contain objects")
            continue
        if dependency.get("actor") not in actor_ids:
            errors.append(f"dependency references unknown actor: {dependency.get('actor')}")
        if dependency.get("beat") not in beat_ids:
            errors.append(f"dependency references unknown beat: {dependency.get('beat')}")
        for key in ("starts_after", "may_overlap", "must_finish_before"):
            for beat_id in dependency.get(key, []) or []:
                if beat_id not in beat_ids:
                    errors.append(f"dependency {key} references unknown beat: {beat_id}")
    return errors
