"""Internal implementation seam for the Motiflux command adapters.

The public surface is the four CLI commands. This module keeps parsing,
fingerprinting, status handling, and safe document I/O in one place so each
adapter stays small and replaceable.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.0"
NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
SUPPORTED_VECTOR_TAGS = {
    "circle",
    "ellipse",
    "line",
    "path",
    "polygon",
    "polyline",
    "rect",
    "text",
    "use",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path | None, payload: Any) -> None:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if path is None:
        print(rendered, end="")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def load_document(path: Path) -> Any:
    """Load JSON, JSON-compatible YAML, or a small YAML subset.

    JSON is preferred because it is deterministic and standard-library only.
    PyYAML is used when installed for normal YAML plans; the fallback parser is
    deliberately conservative and supports the scalar/list/map subset used by
    Motiflux plans.
    """

    text = read_text(path)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(text)
        if parsed is not None:
            return parsed
    except (ImportError, ValueError):
        pass

    return parse_minimal_yaml(text)


def contract_errors(document: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Validate the JSON-Schema subset used by Motiflux without dependencies."""

    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type is not None and not matches_type(document, expected_type):
        errors.append(f"{path} must be of type {expected_type}")
        return errors
    if "const" in schema and document != schema["const"]:
        errors.append(f"{path} must equal {schema['const']!r}")
    if "enum" in schema and document not in schema["enum"]:
        errors.append(f"{path} must be one of {schema['enum']!r}")
    if isinstance(document, str):
        if len(document) < schema.get("minLength", 0):
            errors.append(f"{path} is shorter than minLength")
        pattern = schema.get("pattern")
        if pattern and not re.search(pattern, document):
            errors.append(f"{path} does not match pattern {pattern!r}")
    if isinstance(document, (int, float)) and not isinstance(document, bool):
        if "minimum" in schema and document < schema["minimum"]:
            errors.append(f"{path} is below minimum")
        if "exclusiveMinimum" in schema and document <= schema["exclusiveMinimum"]:
            errors.append(f"{path} is not above exclusiveMinimum")
    if isinstance(document, list):
        if len(document) < schema.get("minItems", 0):
            errors.append(f"{path} has fewer than minItems")
        if "maxItems" in schema and len(document) > schema["maxItems"]:
            errors.append(f"{path} has more than maxItems")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(document):
                errors.extend(contract_errors(item, item_schema, f"{path}[{index}]"))
    if isinstance(document, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in document:
                errors.append(f"{path}.{key} is required")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, child_schema in properties.items():
                if key in document and isinstance(child_schema, dict):
                    errors.extend(contract_errors(document[key], child_schema, f"{path}.{key}"))
        if schema.get("additionalProperties") is False:
            allowed = set(properties) if isinstance(properties, dict) else set()
            for key in document:
                if key not in allowed:
                    errors.append(f"{path}.{key} is not allowed")
    return errors


def matches_type(value: Any, expected: str | list[str]) -> bool:
    expected_types = [expected] if isinstance(expected, str) else expected
    for item in expected_types:
        if item == "null" and value is None:
            return True
        if item == "object" and isinstance(value, dict):
            return True
        if item == "array" and isinstance(value, list):
            return True
        if item == "string" and isinstance(value, str):
            return True
        if item == "boolean" and isinstance(value, bool):
            return True
        if item == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if item == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
    return False


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return None
    if value.startswith("[") or value.startswith("{"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"null", "~"}:
        return None
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except ValueError:
        return value


def strip_yaml_comment(line: str) -> str:
    quote: str | None = None
    for index, char in enumerate(line):
        if char in {'"', "'"}:
            quote = None if quote == char else char if quote is None else quote
        elif char == "#" and quote is None and (index == 0 or line[index - 1].isspace()):
            return line[:index].rstrip()
    return line.rstrip()


def parse_minimal_yaml(text: str) -> Any:
    """Parse the small indentation-oriented subset used by example plans."""

    rows: list[tuple[int, str]] = []
    for raw in text.splitlines():
        cleaned = strip_yaml_comment(raw)
        if not cleaned.strip() or cleaned.lstrip().startswith("---"):
            continue
        indent = len(cleaned) - len(cleaned.lstrip(" "))
        rows.append((indent, cleaned.strip()))
    if not rows:
        return {}

    def parse_block(position: int, indent: int) -> tuple[Any, int]:
        is_list = rows[position][1].startswith("-")
        result: Any = [] if is_list else {}
        while position < len(rows):
            current_indent, content = rows[position]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise ValueError("invalid YAML indentation")
            if is_list:
                if not content.startswith("-"):
                    break
                item = content[1:].strip()
                if not item:
                    if position + 1 < len(rows) and rows[position + 1][0] > indent:
                        value, position = parse_block(position + 1, rows[position + 1][0])
                    else:
                        value, position = None, position + 1
                elif ":" in item and not item.startswith(("\"", "'")):
                    key, raw_value = item.split(":", 1)
                    value = {key.strip(): parse_scalar(raw_value)} if raw_value.strip() else {key.strip(): None}
                    position += 1
                    if position < len(rows) and rows[position][0] > indent:
                        nested, position = parse_block(position, rows[position][0])
                        if isinstance(nested, dict):
                            value.update(nested)
                else:
                    value, position = parse_scalar(item), position + 1
                result.append(value)
                continue

            if ":" not in content:
                raise ValueError(f"expected YAML mapping entry: {content}")
            key, raw_value = content.split(":", 1)
            key = key.strip()
            if raw_value.strip():
                result[key] = parse_scalar(raw_value)
                position += 1
            elif position + 1 < len(rows) and rows[position + 1][0] > indent:
                result[key], position = parse_block(position + 1, rows[position + 1][0])
            else:
                result[key], position = None, position + 1
        return result, position

    parsed, _ = parse_block(0, rows[0][0])
    return parsed


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def number(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    match = NUMBER_RE.search(value)
    return float(match.group(0)) if match else default


def numbers(value: str | None) -> list[float]:
    return [float(item) for item in NUMBER_RE.findall(value or "")]


def parse_viewbox(raw: str | None) -> list[float] | None:
    values = numbers(raw)
    return values if len(values) == 4 else None


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").split())


def canonical_attributes(element: ET.Element, names: Iterable[str]) -> dict[str, str]:
    return {name: normalize_text(element.attrib.get(name)) for name in names if name in element.attrib}


def rect_bounds(element: ET.Element) -> list[float] | None:
    tag = local_name(element.tag)
    a = element.attrib
    if tag == "rect":
        return [number(a.get("x")), number(a.get("y")), number(a.get("width")), number(a.get("height"))]
    if tag == "circle":
        cx, cy, radius = number(a.get("cx")), number(a.get("cy")), number(a.get("r"))
        return [cx - radius, cy - radius, radius * 2, radius * 2]
    if tag == "ellipse":
        cx, cy, rx, ry = number(a.get("cx")), number(a.get("cy")), number(a.get("rx")), number(a.get("ry"))
        return [cx - rx, cy - ry, rx * 2, ry * 2]
    if tag == "line":
        x1, y1, x2, y2 = number(a.get("x1")), number(a.get("y1")), number(a.get("x2")), number(a.get("y2"))
        return [min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)]
    if tag in {"polygon", "polyline"}:
        values = numbers(a.get("points"))
        points = list(zip(values[::2], values[1::2]))
        if points:
            xs, ys = [point[0] for point in points], [point[1] for point in points]
            return [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
    if tag == "path":
        values = numbers(a.get("d"))
        points = list(zip(values[::2], values[1::2]))
        if points:
            xs, ys = [point[0] for point in points], [point[1] for point in points]
            return [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
    return None


def color_of(element: ET.Element) -> str | None:
    for name in ("fill", "stroke", "color"):
        if element.attrib.get(name):
            return normalize_text(element.attrib[name])
    style = element.attrib.get("style", "")
    for declaration in style.split(";"):
        if ":" in declaration:
            key, value = declaration.split(":", 1)
            if key.strip() in {"fill", "stroke", "color"} and value.strip():
                return value.strip()
    return None


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def svg_scene(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    viewbox = parse_viewbox(root.attrib.get("viewBox"))
    if viewbox is None:
        viewbox = [0.0, 0.0, number(root.attrib.get("width")), number(root.attrib.get("height"))]
    records: list[dict[str, Any]] = []
    for index, element in enumerate(root.iter()):
        tag = local_name(element.tag)
        if tag not in SUPPORTED_VECTOR_TAGS:
            continue
        actor_id = element.attrib.get("id") or f"{tag}-{index}"
        path_data = normalize_text(element.attrib.get("d"))
        record = {
            "id": actor_id,
            "tag": tag,
            "bounds": rect_bounds(element),
            "color": color_of(element),
            "fill": normalize_text(element.attrib.get("fill")),
            "stroke": normalize_text(element.attrib.get("stroke")),
            "transform": normalize_text(element.attrib.get("transform")),
            "path_hash": sha256(path_data) if path_data else None,
            "closed": bool(path_data and re.search(r"[zZ]", path_data)),
            "text": normalize_text("".join(element.itertext())) if tag == "text" else None,
        }
        records.append(record)

    canonical = {
        "viewBox": [round(value, 6) for value in viewbox],
        "actor_ids": [item["id"] for item in records],
        "path_data_hashes": [item["path_hash"] for item in records if item["path_hash"]],
        "paint_attributes": [
            {key: item[key] for key in ("id", "fill", "stroke", "color")}
            for item in records
        ],
        "transform_matrices": [item["transform"] for item in records],
        "layer_order": [item["id"] for item in records],
    }
    canonical["fingerprint"] = sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")))
    return {
        "viewbox": viewbox,
        "records": records,
        "canonical": canonical,
        "topology": {
            "element_count": len(records),
            "path_count": sum(item["tag"] == "path" for item in records),
            "closed_path_count": sum(item["closed"] for item in records),
            "text_count": sum(item["tag"] == "text" for item in records),
            "component_count": len(records),
        },
        "colors": sorted({item["color"] for item in records if item["color"]}),
    }


def format_value(value: Any) -> Any:
    if isinstance(value, float) and math.isclose(value, round(value), abs_tol=1e-9):
        return int(round(value))
    return value


def source_format(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return "jpeg" if suffix == "jpg" else suffix if suffix in {"svg", "png", "jpeg", "webp"} else "unknown"


def parse_raster_header(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    fmt = source_format(path)
    width: int | None = None
    height: int | None = None
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 26:
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP" and len(data) >= 30:
        chunk = data[12:16]
        if chunk == b"VP8X":
            width = 1 + int.from_bytes(data[24:27], "little")
            height = 1 + int.from_bytes(data[27:30], "little")
    elif data[:2] == b"\xff\xd8":
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            index += 2
            if marker in {0xD8, 0xD9}:
                continue
            size = int.from_bytes(data[index:index + 2], "big")
            if marker in set(range(0xC0, 0xC4)) | set(range(0xC5, 0xC8)) | set(range(0xC9, 0xCC)) | set(range(0xCD, 0xD0)):
                height = int.from_bytes(data[index + 3:index + 5], "big")
                width = int.from_bytes(data[index + 5:index + 7], "big")
                break
            index += max(size, 2)
    return {"format": fmt, "width": width, "height": height, "header_bytes": min(len(data), 64)}
