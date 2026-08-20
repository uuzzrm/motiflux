"""Create a contract-valid motion plan from source observations and a theme."""

from __future__ import annotations

import re
from typing import Any

from .catalog import ThemeProfile


TRAJECTORY_BEATS = {
    "knowledge-graph-lock": ("map", "connect", "lock"),
    "contour-etch": ("trace", "etch", "resolve"),
    "token-commit": ("parse", "commit", "publish"),
    "signal-convergence": ("seed", "converge", "land"),
    "progress-confirm": ("measure", "confirm", "settle"),
    "boundary-unlock": ("guard", "verify", "unlock"),
    "burst-assembly": ("compress", "release", "idle"),
    "kinematic-lock": ("prime", "drive", "lock"),
    "impact-release": ("load", "impact", "recover"),
    "aperture-title": ("darken", "open", "hold"),
    "organic-current": ("breathe", "flow", "root"),
    "orbit-quest": ("spawn", "assemble", "clear"),
    "semantic-fade": ("show", "signal", "rest"),
}

FOREGROUND_STAGE_ORDER = ("seed", "trace", "assemble", "lockup", "canonical")

ROLE_ORDER = ("origin-dot", "arc", "bar", "monogram", "wordmark", "unknown")
ROLE_PRIORITY = {role: index for index, role in enumerate(ROLE_ORDER)}
ROLE_ALIASES = {
    "dot": "origin-dot",
    "origin": "origin-dot",
    "origin-dot": "origin-dot",
    "spark": "origin-dot",
    "arc": "arc",
    "curve": "arc",
    "bar": "bar",
    "line": "bar",
    "monogram": "monogram",
    "letter": "monogram",
    "wordmark": "wordmark",
    "text": "wordmark",
}

DIRECTION_VECTORS = {
    "left-to-right": (1, 0),
    "right-to-left": (-1, 0),
    "top-to-bottom": (0, 1),
    "bottom-to-top": (0, -1),
    "radial": (0, 0),
}


def _parse_surface(text: str) -> str:
    """Map explicit delivery words to the small set of supported surfaces."""

    if any(term in text for term in ("showcase", "atlas", "展示", "对比网格")):
        return "showcase"
    if any(term in text for term in ("splash", "开屏", "启动页")):
        return "splash"
    if any(term in text for term in ("loading", "loader", "加载")):
        return "loading"
    if any(term in text for term in ("idle", "待机")):
        return "idle"
    return "web-intro"


def _record_request_constraints(text: str) -> list[dict[str, str]]:
    """Keep renderer-specific wishes visible instead of silently dropping them."""

    constraints: list[dict[str, str]] = []
    requests = (
        ("glow-policy", ("glow", "发光", "光晕"), "visual", "cosmetic", "glow preference requires a renderer adapter"),
        ("contrast-policy", ("high contrast", "contrast", "高对比度", "对比度"), "accessibility", "structural", "contrast preference requires visual QA"),
        ("keyboard-proof", ("keyboard", "键盘", "focus", "焦点"), "accessibility", "structural", "keyboard and focus behavior requires accessibility-tree QA"),
        ("pause-timing", ("pause at", "pause on", "暂停在", "暂停后"), "interaction", "structural", "timed pause requires a runtime capture adapter"),
        ("video-export", ("mp4", "webm", "视频"), "output", "cosmetic", "video export is not provided by the current offline adapters"),
        ("low-motion-policy", ("low-amplitude", "low amplitude", "no overshoot", "opacity-first", "低动效", "低幅度", "无过冲"), "motion", "structural", "low-amplitude, no-overshoot, and opacity-first preferences require renderer support"),
        ("particle-policy", ("sparse secondary particles", "dense particles", "粒子密度", "稀疏粒子", "密集粒子", "seed ", "种子"), "visual", "cosmetic", "particle density and seed are recorded for an adapter; the generic runtime only guarantees the on/off switch"),
    )
    for constraint_id, terms, kind, importance, target in requests:
        if any(term in text for term in terms):
            constraints.append(
                {
                    "id": constraint_id,
                    "kind": kind,
                    "importance": importance,
                    "target": target,
                    "status": "recorded-unresolved",
                    "source": "request",
                }
            )
    return constraints


def _normalise_role(value: object) -> str:
    key = str(value or "").strip().casefold().replace("_", "-").replace(" ", "-")
    return ROLE_ALIASES.get(key, "unknown")


def _is_raster_record(record: dict[str, Any], raster_source: bool = False) -> bool:
    """Identify records whose roles are only pixel observations."""

    return raster_source or str(record.get("geometry_strategy", "")).casefold() == "pixel-observation-only" or str(record.get("tag", "")).casefold() == "raster-component"


def _record_role(
    record: dict[str, Any],
    role_hint: str | None = None,
    *,
    raster_source: bool = False,
) -> tuple[str, str, str, str, str | None]:
    """Return a role candidate and the evidence used to choose it.

    Explicit raster candidates win. Vector heuristics are intentionally modest:
    they classify only obvious text, line-like, or small circular actors and
    leave everything else as ``unknown`` for review.
    """

    candidates = record.get("role_candidates")
    review = record.get("role_review") if isinstance(record.get("role_review"), dict) else {}
    # An explicit reviewer annotation is stronger than a geometric hint. The
    # nested review record is the canonical handoff for raster observations;
    # the flat fields remain supported for older source-analysis artifacts.
    review_status = str(review.get("review_status", "")).strip().casefold()
    evidence = str(review.get("evidence") or record.get("role_basis", "")).strip()
    accepted = _normalise_role(review.get("accepted_role"))
    if accepted == "unknown":
        accepted = _normalise_role(record.get("accepted_role"))

    # Raster geometry and role scores are observations, not semantic bindings.
    # Keep the proposal in the evidence while exposing only the unknown
    # sentinel until an explicit accepted review is present.
    if _is_raster_record(record, raster_source):
        if accepted != "unknown" and review_status == "accepted" and evidence:
            return (
                accepted,
                evidence,
                str(review.get("confidence") or record.get("role_confidence", "medium")),
                "accepted",
                accepted,
            )
        proposed = _normalise_role(review.get("proposed_role"))
        if proposed != "unknown":
            return (
                "unknown",
                str(review.get("evidence") or f"unconfirmed raster role proposal: {proposed}"),
                str(review.get("confidence", "low")),
                "needs-review",
                None,
            )
        return (
            "unknown",
            evidence or "raster role is unconfirmed; geometric observation is not semantic evidence",
            "low",
            "needs-review",
            None,
        )

    if accepted != "unknown" and review_status == "accepted" and evidence:
        return (
            accepted,
            evidence,
            str(review.get("confidence") or record.get("role_confidence", "medium")),
            "accepted",
            accepted,
        )
    proposed = _normalise_role(review.get("proposed_role"))
    if proposed != "unknown":
        return (
            proposed,
            str(review.get("evidence", "nested role_review proposal")),
            str(review.get("confidence", "low")),
            str(review.get("review_status", "needs-review")),
            None,
        )
    hinted = _normalise_role(role_hint)
    if hinted != "unknown":
        return (
            hinted,
            "bounded geometric group heuristic; semantic role still requires review",
            "low",
            "needs-review",
            None,
        )
    if isinstance(candidates, list):
        for candidate in candidates:
            value = candidate.get("role") if isinstance(candidate, dict) else candidate
            role = _normalise_role(value)
            if role != "unknown":
                confidence = str(candidate.get("confidence", "low")) if isinstance(candidate, dict) else "low"
                basis = str(candidate.get("basis", f"source-analysis role candidate ({confidence})")) if isinstance(candidate, dict) else f"source-analysis role candidate ({confidence})"
                return role, basis, confidence, "needs-review", None
    explicit = _normalise_role(record.get("role"))
    if explicit != "unknown":
        confidence = "medium"
        for candidate in candidates or []:
            if isinstance(candidate, dict) and _normalise_role(candidate.get("role")) == explicit:
                confidence = str(candidate.get("confidence", confidence))
                break
        return explicit, "explicit source-analysis role", confidence, "needs-review", None

    tag = str(record.get("tag", "")).casefold()
    bounds = record.get("bounds")
    width = float(bounds[2]) if isinstance(bounds, list) and len(bounds) >= 4 and isinstance(bounds[2], (int, float)) else 0.0
    height = float(bounds[3]) if isinstance(bounds, list) and len(bounds) >= 4 and isinstance(bounds[3], (int, float)) else 0.0
    aspect = width / height if height > 0 else 0.0
    if tag == "text":
        return "wordmark", "SVG text element", "medium", "needs-review", None
    if tag == "line" or (width > 0 and height > 0 and aspect >= 4.0):
        return "bar", "line-like source bounds", "medium", "needs-review", None
    if tag in {"circle", "ellipse"} and max(width, height) > 0 and max(width, height) / max(1.0, min(width, height)) < 1.6:
        if str(record.get("fill", "")).casefold() in {"none", "transparent"} and record.get("stroke"):
            return "arc", "outlined circular source actor", "medium", "needs-review", None
        return "origin-dot", "compact circular source actor", "medium", "needs-review", None
    if tag in {"path", "polyline", "polygon"} and width > 0 and height > 0 and aspect >= 1.5:
        return "arc", "wide curved/vector source actor", "low", "needs-review", None
    return "unknown", "insufficient geometric evidence", "low", "needs-review", None


def _candidate_score(record: dict[str, Any], role: str) -> float:
    """Read a geometric role score without treating it as semantic truth."""

    for candidate in record.get("role_candidates", []) or []:
        if isinstance(candidate, dict) and _normalise_role(candidate.get("role")) == role:
            try:
                return float(candidate.get("score", 0.0))
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def _geometric_role_hints(records: list[dict[str, Any]]) -> dict[str, str]:
    """Derive conservative group-local hints for raster components.

    Connected-component scoring is intentionally weak in isolation: a small
    wordmark glyph can look like a dot, while a symbol can look like a wide
    curve.  Use the already observed layout groups and relative component
    size to improve the provisional stage order.  These hints stay
    ``needs-review`` in the plan and never become accepted semantic labels.
    """

    raster_records = [
        record
        for record in records
        if isinstance(record, dict) and record.get("layout_group") in {"symbol", "wordmark"}
    ]
    hints: dict[str, str] = {}
    wordmark = [record for record in raster_records if record.get("layout_group") == "wordmark"]
    for record in wordmark:
        actor_id = str(record.get("id", ""))
        if actor_id:
            hints[actor_id] = "wordmark"

    symbol = [record for record in raster_records if record.get("layout_group") == "symbol"]
    if not symbol:
        return hints

    def area(record: dict[str, Any]) -> float:
        try:
            return float(record.get("area", 0.0))
        except (TypeError, ValueError):
            return 0.0

    compact = [
        record
        for record in symbol
        if isinstance(record.get("bounds"), list)
        and len(record["bounds"]) == 4
        and max(float(record["bounds"][2]), float(record["bounds"][3]))
        / max(1.0, min(float(record["bounds"][2]), float(record["bounds"][3])))
        < 1.65
    ]
    if len(symbol) < 2:
        return hints
    compact = [
        record
        for record in compact
        if _candidate_score(record, "origin-dot") >= 0.65
    ]
    if not compact:
        return hints
    dot = min(compact, key=area)
    dot_id = str(dot.get("id", ""))
    if dot_id:
        hints[dot_id] = "origin-dot"

    remaining = [record for record in symbol if record is not dot]
    if not remaining:
        return hints
    arc = max(remaining, key=lambda record: (_candidate_score(record, "arc"), -area(record)))
    arc_id = str(arc.get("id", ""))
    if arc_id:
        hints[arc_id] = "arc"
    for record in remaining:
        actor_id = str(record.get("id", ""))
        if actor_id and actor_id not in hints:
            hints[actor_id] = "monogram" if _candidate_score(record, "monogram") >= _candidate_score(record, "arc") else "unknown"
    return hints


def _construction_order(
    records: list[dict[str, Any]],
    actor_ids: list[str],
    *,
    raster_source: bool = False,
) -> tuple[list[str], dict[str, dict[str, str]]]:
    by_id = {str(record.get("id")): record for record in records if isinstance(record, dict) and record.get("id")}
    role_hints = _geometric_role_hints(records)
    annotations: dict[str, dict[str, str]] = {}
    indexed = []
    for index, actor_id in enumerate(actor_ids):
        role, basis, confidence, review_status, accepted_role = _record_role(
            by_id.get(actor_id, {"id": actor_id}),
            role_hints.get(actor_id),
            raster_source=raster_source,
        )
        annotations[actor_id] = {
            "role": role,
            "selected_role": role,
            "basis": basis,
            "confidence": confidence,
            "review_status": review_status,
            "accepted_role": accepted_role,
        }
        indexed.append((ROLE_PRIORITY.get(role, ROLE_PRIORITY["unknown"]), index, actor_id))
    indexed.sort()
    return [actor_id for _, _, actor_id in indexed], annotations


def parse_runtime_controls(request: str, profile: ThemeProfile) -> dict[str, Any]:
    """Parse bounded, deterministic controls from a natural-language request."""

    text = str(request or "").casefold()
    tempo = float(profile.runtime.get("tempo", 1.0))
    duration_ms = 1400
    duration_match = re.search(r"(?<!\d)(\d+(?:\.\d+)?)\s*(ms|milliseconds?|毫秒|s|sec(?:onds?)?|秒)", text)
    if duration_match:
        amount = float(duration_match.group(1))
        duration_ms = round(amount if duration_match.group(2).startswith(("ms", "毫")) else amount * 1000)
    tempo_match = re.search(r"(?:tempo|speed|速度|节奏)\s*(?:is|=|:)?\s*(\d+(?:\.\d+)?)\s*x\b", text)
    if tempo_match is None:
        # Accept the compact form users commonly write in a mixed prompt:
        # ``1.25x``.  Keep the token bounded so dimensions such as ``16x9``
        # are not mistaken for playback speed.
        tempo_match = re.search(r"(?<![\w.])(\d+(?:\.\d+)?)\s*x\b", text)
    if tempo_match:
        tempo = float(tempo_match.group(1))
    elif any(token in text for token in ("slow", "slow motion", "慢速", "慢一点", "舒缓")):
        tempo *= 0.72
    elif any(token in text for token in ("fast", "quick", "rapid", "快速", "快一点", "有冲击力")):
        tempo *= 1.3
    tempo = max(0.25, min(4.0, round(tempo, 3)))
    duration_ms = max(240, min(12000, duration_ms))

    direction = "radial"
    direction_terms = (
        (("left to right", "left-to-right", "从左到右", "由左向右"), "left-to-right"),
        (("right to left", "right-to-left", "从右到左", "由右向左"), "right-to-left"),
        (("top to bottom", "top-to-bottom", "从上到下", "由上向下"), "top-to-bottom"),
        (("bottom to top", "bottom-to-top", "从下到上", "由下向上"), "bottom-to-top"),
        (("center outward", "center-outward", "center to outward", "中心向外", "由中心向外"), "radial"),
    )
    for terms, value in direction_terms:
        if any(term in text for term in terms):
            direction = value
            break
    if any(term in text for term in ("clockwise", "顺时针", "orbit")):
        direction = "radial"

    hex_match = re.search(r"#[0-9a-f]{3,8}\b", text)
    if any(term in text for term in ("transparent", "no background", "无背景", "透明背景")):
        background = {"mode": "transparent", "color": "transparent", "source": "prompt"}
    elif any(term in text for term in ("solid", "pure color", "纯色", "纯色背景", "单色背景")):
        background = {
            "mode": "solid",
            "color": hex_match.group(0) if hex_match else "#0b0d12",
            "source": "prompt" if hex_match else "default",
        }
    else:
        background = {"mode": "theme", "color": None, "source": "theme-profile"}

    particles = not any(term in text for term in ("no particles", "without particles", "particle-free", "不要粒子", "关闭粒子", "无粒子"))
    if any(term in text for term in ("sparse secondary particles", "sparse particles", "稀疏粒子")):
        particle_density = "sparse"
    elif any(term in text for term in ("dense particles", "heavy particles", "密集粒子")):
        particle_density = "dense"
    else:
        particle_density = "standard"
    seed_match = re.search(r"(?:seed|种子)\s*(?:is|=|:)?\s*(\d+)\b", text)
    seed = int(seed_match.group(1)) if seed_match else 0
    seed = max(0, min(2147483647, seed))
    if any(term in text for term in ("opacity-only", "opacity only", "仅透明度", "只改变透明度")):
        reduced_motion = "opacity-only"
    elif any(term in text for term in ("full motion", "allow motion", "完整动效", "允许动效")):
        reduced_motion = "user-choice"
    else:
        reduced_motion = "static-canonical"
    requested_formats = [name for name, terms in {
        "gif": ("gif", "动图", "gif格式"),
        "html": ("html", "网页包", "web package"),
        "svg": ("svg", "矢量"),
        "pdf": ("pdf", "pdf展示", "图册"),
    }.items() if any(term in text for term in terms)]
    if not requested_formats:
        requested_formats = ["html", "svg"]
    return {
        "duration_ms": duration_ms,
        "tempo": tempo,
        "direction": direction,
        "direction_vector": list(DIRECTION_VECTORS[direction]),
        "particles": particles,
        "particle_density": particle_density,
        "seed": seed,
        "background": background,
        "reduced_motion": reduced_motion,
        "requested_formats": requested_formats,
        "surface": _parse_surface(text),
        "request_constraints": _record_request_constraints(text),
    }


def build_foreground_plan(
    actor_ids: list[str],
    profile: ThemeProfile,
    records: list[dict[str, Any]] | None = None,
    *,
    source_format: str | None = None,
) -> dict[str, Any]:
    """Build the machine-readable source-actor construction contract."""

    source_actors = list(actor_ids or ["mark"])
    raster_source = str(source_format or "").casefold() in {"png", "jpg", "jpeg", "webp"}
    construction_actors, role_annotations = _construction_order(
        records or [], source_actors, raster_source=raster_source
    )
    layout_groups = {
        "symbol": [str(record.get("id")) for record in records or [] if record.get("layout_group") == "symbol"],
        "wordmark": [str(record.get("id")) for record in records or [] if record.get("layout_group") == "wordmark"],
    }
    role_to_stage = {
        "origin-dot": "seed",
        "arc": "trace",
        "bar": "assemble",
        "monogram": "lockup",
        "wordmark": "lockup",
        # An unconfirmed raster role is evidence, not a dynamic actor. Keep
        # it outside the generic stage map so the runtime can honor the
        # static-canonical fallback until explicit review accepts the binding.
        "unknown": "canonical",
    }
    actor_stage_map = {
        actor_id: role_to_stage.get(role_annotations.get(actor_id, {}).get("role", "unknown"), "canonical")
        for actor_id in source_actors
    }
    tempo = float(profile.runtime.get("tempo", 1.0))
    damping = float(profile.runtime.get("settle_damping", 0.82))
    catalog_plan = dict(profile.foreground_plan or {})
    path_strategies = {
        "seed": "source-point",
        "trace": str(catalog_plan.get("path_strategy") or f"measured-{profile.trajectory_id}"),
        "assemble": str(catalog_plan.get("path_strategy") or f"{profile.trajectory_id}-component-assembly"),
        "lockup": "source-actor-order",
        "canonical": str(catalog_plan.get("fallback") or "static-canonical"),
    }
    phase_names = {
        "seed": "entry",
        "trace": "theme-paced",
        "assemble": "staggered",
        "lockup": "settle",
        "canonical": "hold",
    }

    stages: list[dict[str, Any]] = []
    for stage_id in FOREGROUND_STAGE_ORDER:
        if stage_id == "seed":
            stage_actors = construction_actors[:1]
        elif stage_id == "trace":
            stage_actors = construction_actors[: max(1, min(len(construction_actors), 2))]
        elif stage_id == "assemble":
            stage_actors = construction_actors[: max(1, len(construction_actors) - 1)]
        else:
            stage_actors = list(source_actors)
        stages.append(
            {
                "id": stage_id,
                "source_actors": stage_actors,
                "role_annotations": {actor_id: role_annotations.get(actor_id, {"role": "unknown", "selected_role": "unknown", "basis": "unresolved", "confidence": "low", "review_status": "needs-review", "accepted_role": None}) for actor_id in stage_actors},
                "path_strategy": path_strategies[stage_id],
                "speed_profile": {
                    "tempo": tempo,
                    "settle_damping": damping,
                    "phase": phase_names[stage_id],
                },
                "role_bindings": [
                    {
                        "actor_id": actor_id,
                        "role": role_annotations.get(actor_id, {}).get("role", "unknown"),
                        "selected_role": role_annotations.get(actor_id, {}).get("selected_role", "unknown"),
                        "confidence": role_annotations.get(actor_id, {}).get("confidence", "low"),
                        "review_status": role_annotations.get(actor_id, {}).get("review_status", "needs-review"),
                        "accepted_role": role_annotations.get(actor_id, {}).get("accepted_role"),
                        "evidence": role_annotations.get(actor_id, {}).get("basis", "unresolved"),
                    }
                    for actor_id in stage_actors
                ],
                "visible_proof": {
                    "criterion": f"{stage_id} exposes only source-derived actors",
                    "source_actor_count": len(stage_actors),
                },
            }
        )
    return {
        "source_actors": source_actors,
        "construction_order": construction_actors,
        "role_annotations": role_annotations,
        "layout_groups": layout_groups,
        "actor_stage_map": actor_stage_map,
        "mapping_policy": "role candidates choose a provisional stage; low-confidence raster roles remain needs-review",
        "stage_order": list(FOREGROUND_STAGE_ORDER),
        "stages": stages,
        "proof": {
            "trajectory_id": profile.trajectory_id,
            "identity_rule": "source actor geometry is never redrawn",
            "canonical_rule": "canonical stage uses the source geometry and paint",
        },
        "static_canonical_fallback": {
            "mode": "static-canonical",
            "source_actors": source_actors,
            "trigger": "prefers-reduced-motion or unavailable trajectory adapter",
        },
        "foreground_mode": str(catalog_plan.get("mode", "source-derived")),
        "foreground_variant": str(catalog_plan.get("variant", "default")),
        "foreground_timing": str(catalog_plan.get("timing", "declared")),
        "foreground_easing": str(catalog_plan.get("easing", "linear")),
        "path_strategy": str(catalog_plan.get("path_strategy") or f"measured-{profile.trajectory_id}"),
        "speed_profile": str(catalog_plan.get("speed_profile") or "declared route timing"),
    }


def foreground_evidence(plan: dict[str, Any]) -> dict[str, Any]:
    """Turn a foreground plan into explicit, non-invented evidence records."""

    foreground = plan.get("foreground_plan", {})
    actor_records = {
        str(actor.get("id")): actor
        for actor in plan.get("actors", [])
        if isinstance(actor, dict) and actor.get("id")
    }
    snapshots = []
    review_statuses: list[str] = []
    for stage in foreground.get("stages", []) if isinstance(foreground, dict) else []:
        if not isinstance(stage, dict):
            continue
        actor_ids = [str(actor_id) for actor_id in stage.get("source_actors", []) or []]
        actor_geometry = []
        bounds: list[list[float]] = []
        area = 0.0
        for actor_id in actor_ids:
            actor = actor_records.get(actor_id, {})
            source_bounds = actor.get("source_bounds")
            if isinstance(source_bounds, list) and len(source_bounds) == 4:
                bounds.append([float(value) for value in source_bounds])
            source_area = actor.get("source_area")
            if isinstance(source_area, (int, float)) and not isinstance(source_area, bool):
                area += float(source_area)
            binding = next((item for item in stage.get("role_bindings", []) if isinstance(item, dict) and item.get("actor_id") == actor_id), {})
            review_status = str(binding.get("review_status", "needs-review"))
            review_statuses.append(review_status)
            actor_geometry.append({
                "actor_id": actor_id,
                "bounds": source_bounds,
                "area": source_area,
                "role": binding.get("role", actor.get("role", "unknown")),
                "review_status": review_status,
                "accepted_role": binding.get("accepted_role"),
            })
        union = None
        if bounds:
            left = min(item[0] for item in bounds)
            top = min(item[1] for item in bounds)
            right = max(item[0] + item[2] for item in bounds)
            bottom = max(item[1] + item[3] for item in bounds)
            union = {"x": left, "y": top, "width": right - left, "height": bottom - top}
        snapshots.append(
            {
                "stage_id": stage.get("id"),
                "source_actor_ids": actor_ids,
                "foreground_bounds": {"source": "motion-plan actor observations", "status": "observed" if union else "unresolved", "value": union},
                "alpha_mass": area or None,
                "actor_geometry": actor_geometry,
                "path_strategy": stage.get("path_strategy"),
                "speed_profile": stage.get("speed_profile", {}),
                "proof": stage.get("visible_proof", {}),
            }
        )
    return {
        "status": "observed" if snapshots and all(item.get("foreground_bounds", {}).get("status") == "observed" for item in snapshots) else "declared",
        "source_actor_ids": list(foreground.get("source_actors", [])) if isinstance(foreground, dict) else [],
        "stage_order": list(foreground.get("stage_order", [])) if isinstance(foreground, dict) else [],
        "stage_snapshots": snapshots,
        "canonical_stage": "canonical",
        "identity_source": "source actors and canonical source paint",
        "role_review": "accepted" if review_statuses and all(status == "accepted" for status in review_statuses) else "needs-review",
    }


def build_plan(source_analysis: dict[str, Any], selection: dict[str, Any], profile: ThemeProfile, *, project_name: str, source_name: str, request: str = "") -> dict[str, Any]:
    records = source_analysis.get("observations", {}).get("elements", [])
    actor_ids = [str(item.get("id")) for item in records if isinstance(item, dict) and item.get("id")]
    if not actor_ids:
        actor_ids = ["mark"]
    try:
        beat_ids = TRAJECTORY_BEATS[profile.trajectory_id]
    except KeyError as error:
        raise ValueError(f"unimplemented trajectory: {profile.trajectory_id}") from error
    runtime_controls = parse_runtime_controls(request, profile)
    surface = str(runtime_controls.pop("surface", "web-intro"))
    request_constraints = list(runtime_controls.pop("request_constraints", []))
    source_format = str(source_analysis.get("source", {}).get("format", "")).casefold()
    foreground_plan = build_foreground_plan(
        actor_ids,
        profile,
        records,
        source_format=source_format,
    )
    recognition = source_analysis.get("observations", {}).get("recognition")
    if not isinstance(recognition, dict):
        raster = source_analysis.get("observations", {}).get("raster", {})
        recognition = raster.get("recognition") if isinstance(raster, dict) else None
    foreground_plan["recognition_handoff"] = recognition if isinstance(recognition, dict) else {
        "mode": "unavailable",
        "review_status": "needs-review",
        "input_boundary": "source recognition evidence was not available",
        "decision_trace": ["retain source actors as candidates", "use static-canonical fallback when binding is uncertain"],
    }
    geometry_strategy = "preserve-source-vector" if source_format == "svg" else "pixel-observation-only"
    source_observation = "observed-vector-geometry" if source_format == "svg" else "observed-raster-components"
    beat_defs = [
        {"id": beat_ids[0], "intent": f"establish the {profile.trajectory_id} entry state", "duration_weight": 1},
        {"id": beat_ids[1], "intent": f"apply the {profile.id} foreground construction to identity-bearing actors", "duration_weight": 2},
        {"id": beat_ids[2], "intent": "settle into the canonical mark without changing identity", "duration_weight": 1},
    ]
    property_channels = ["opacity", "transform", "secondary-effect", f"trajectory:{profile.trajectory_id}"]
    actors = [
        {
            "id": actor_id,
            "role": foreground_plan.get("role_annotations", {}).get(actor_id, {}).get("role", "unknown"),
            "selected_role": foreground_plan.get("role_annotations", {}).get(actor_id, {}).get("selected_role", "unknown"),
            "role_confidence": foreground_plan.get("role_annotations", {}).get(actor_id, {}).get("confidence", "low"),
            "role_review_status": foreground_plan.get("role_annotations", {}).get(actor_id, {}).get("review_status", "needs-review"),
            "accepted_role": foreground_plan.get("role_annotations", {}).get(actor_id, {}).get("accepted_role"),
            "geometry_strategy": geometry_strategy,
            "trajectory_strategy": profile.trajectory_id,
            "parent": None,
            "anchor": "source-bounds",
            "layer": index,
            "occludes": [],
            "occluded_by": [],
            "role_basis": foreground_plan.get("role_annotations", {}).get(actor_id, {}).get("basis", "unresolved"),
            "source_bounds": next((item.get("bounds") for item in records if isinstance(item, dict) and str(item.get("id")) == actor_id and isinstance(item.get("bounds"), list)), None),
            "source_area": next((item.get("area") for item in records if isinstance(item, dict) and str(item.get("id")) == actor_id and isinstance(item.get("area"), (int, float))), None),
            "source_observation": source_observation if any(isinstance(item, dict) and str(item.get("id")) == actor_id and item.get("bounds") for item in records) else "unresolved",
        }
        for index, actor_id in enumerate(actor_ids)
    ]
    dependencies = [
        {
            "actor": actor_id,
            "beat": beat_ids[1],
            "starts_after": [beat_ids[0]],
            "may_overlap": [],
            "must_finish_before": [beat_ids[2]],
            "anchor": "source-bounds",
            "property_channels": property_channels,
        }
        for actor_id in actor_ids
    ]
    return {
        "schema_version": "1.0",
        "project": {"name": project_name, "surface": surface, "source": source_name},
        "theme_selection": {
            **selection["theme_selection"],
            "catalog_id": "motiflux-motion-themes",
            "primary_id": profile.id,
            "trajectory_id": profile.trajectory_id,
            "trajectory_summary": profile.trajectory_summary,
        },
        "motion_language": {
            "traits": [
                {"name": "tempo", "value": profile.runtime.get("tempo", 1.0), "trace": profile.algorithm_stack[0]},
                {"name": "settle", "value": profile.runtime.get("settle_damping", 0.82), "trace": "canonical end-state requirement"},
                {"name": "secondary-effect", "value": profile.runtime.get("secondary_effect", "plain"), "trace": profile.algorithm_stack[-1]},
                {"name": "foreground-trajectory", "value": profile.trajectory_id, "trace": profile.trajectory_summary},
            ],
            "design_intent": profile.design_intent,
            "implementation_controls": list(profile.controls),
        },
        "constraints": [
            {"id": "identity-source", "kind": "topology", "importance": "identity", "target": "preserve source actor IDs and canonical paint", "tolerance": 0},
            {"id": "canonical-end-state", "kind": "landmark", "importance": "identity", "target": "exact source vector fingerprint after finish", "tolerance": 0},
            *request_constraints,
        ],
        "foreground_plan": foreground_plan,
        "actors": actors,
        "beats": beat_defs,
        "dependencies": dependencies,
        "runtime": {
            **runtime_controls,
            "settle_damping": profile.runtime.get("settle_damping", 0.82),
            "secondary_effect": profile.runtime.get("secondary_effect", "plain"),
            "trajectory_id": profile.trajectory_id,
            "controls": ["play", "pause", "replay", "tempo", "duration", "direction", "background", "particles", "reduced_motion"],
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

    foreground = plan.get("foreground_plan")
    if not isinstance(foreground, dict):
        errors.append("foreground_plan is required")
    else:
        stage_order = [str(item) for item in foreground.get("stage_order", [])]
        stage_records = [item for item in foreground.get("stages", []) if isinstance(item, dict)]
        stage_ids = [str(stage.get("id")) for stage in stage_records]
        if stage_order != stage_ids:
            errors.append("foreground_plan stage_order must match stages")
        for stage in stage_records:
            for actor_id in stage.get("source_actors", []) or []:
                if actor_id not in actor_ids:
                    errors.append(f"foreground stage references unknown actor: {actor_id}")
    return errors
