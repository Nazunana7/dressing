from __future__ import annotations

import re
from typing import Any, Iterable

from .models import ProposedOperation, WardrobeItem

ALLOWED_UPDATE_FIELDS = {
    "name",
    "category",
    "subtype",
    "colors",
    "materials",
    "pattern",
    "fit",
    "style_tags",
    "formality",
    "seasons",
    "thickness",
    "scenes",
    "restrictions",
    "notes",
    "inference_status",
}


def slugify(value: str, fallback: str = "item") -> str:
    text = value.strip().lower()
    text = re.sub(r"[\s/]+", "-", text)
    text = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff_-]+", "", text)
    return text or fallback


def compact_items(items: Iterable[WardrobeItem]) -> list[dict[str, Any]]:
    return [
        item.model_dump(
            include={
                "id",
                "name",
                "category",
                "subtype",
                "colors",
                "materials",
                "pattern",
                "fit",
                "style_tags",
                "formality",
                "seasons",
                "thickness",
                "scenes",
                "restrictions",
                "notes",
                "inference_status",
            },
            mode="json",
        )
        for item in items
    ]


def apply_operation(items: list[WardrobeItem], operation: ProposedOperation) -> tuple[list[WardrobeItem], str]:
    if operation.op == "add":
        if not operation.item:
            raise ValueError("新增衣物缺少 item 数据")
        raw = dict(operation.item)
        raw.setdefault("inference_status", "confirmed")
        if not raw.get("id"):
            raw["id"] = slugify(str(raw.get("name", "item")))
        item = WardrobeItem.model_validate(raw)
        if any(existing.id == item.id for existing in items):
            raise ValueError(f"衣物 ID 已存在: {item.id}")
        return [*items, item], f"已新增 {item.name}"

    if operation.op == "update":
        if not operation.item_id:
            raise ValueError("修改衣物缺少 item_id")
        idx = next((i for i, item in enumerate(items) if item.id == operation.item_id), None)
        if idx is None:
            raise ValueError(f"找不到衣物: {operation.item_id}")
        allowed = {key: value for key, value in operation.fields.items() if key in ALLOWED_UPDATE_FIELDS}
        updated = items[idx].model_copy(update=allowed)
        new_items = list(items)
        new_items[idx] = updated
        return new_items, f"已修改 {updated.name}"

    if operation.op == "delete":
        if not operation.item_id:
            raise ValueError("删除衣物缺少 item_id")
        existing = next((item for item in items if item.id == operation.item_id), None)
        if existing is None:
            raise ValueError(f"找不到衣物: {operation.item_id}")
        return [item for item in items if item.id != operation.item_id], f"已删除 {existing.name}"

    raise ValueError(f"不支持的操作: {operation.op}")


def summarize_operations(operations: list[ProposedOperation]) -> str:
    labels = {"add": "新增", "update": "修改", "delete": "删除"}
    lines = []
    for operation in operations:
        if operation.op == "add" and operation.item:
            lines.append(f"- 新增: {operation.item.get('name') or '未命名单品'}")
        elif operation.op in {"update", "delete"}:
            lines.append(f"- {labels[operation.op]}: {operation.item_id}")
    return "\n".join(lines)


def wardrobe_context_lines(items: Iterable[WardrobeItem]) -> list[str]:
    """Return a compact line format that keeps request context small."""
    lines: list[str] = []
    for item in items:
        fields = [
            item.id,
            item.name,
            item.category,
            item.subtype or "-",
            "/".join(item.colors) or "-",
            "/".join(item.materials) or "-",
            item.thickness,
            "/".join(item.seasons) or "-",
            "/".join(item.scenes) or "-",
            str(item.formality),
            "/".join(item.style_tags) or "-",
        ]
        extra = "；".join(item.restrictions)
        if item.notes:
            extra = f"{extra}；{item.notes[:80]}" if extra else item.notes[:80]
        fields.append(extra or "-")
        lines.append(" | ".join(fields))
    return lines


THICKNESS_ALIASES = {
    "未知": "unknown",
    "unknown": "unknown",
    "超薄": "sheer",
    "透视": "sheer",
    "轻薄": "light",
    "薄": "light",
    "light": "light",
    "中等": "medium",
    "适中": "medium",
    "medium": "medium",
    "厚": "thick",
    "厚重": "thick",
    "thick": "thick",
}


def _as_list(value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in re.split(r"[,，/、]", str(value)) if part.strip()]


def _normalize_field_aliases(raw: dict[str, Any]) -> dict[str, Any]:
    aliases = {
        "subcategory": "subtype",
        "color": "colors",
        "colors": "colors",
        "material": "materials",
        "materials": "materials",
        "scenario": "scenes",
        "scenarios": "scenes",
        "scene": "scenes",
        "scenes": "scenes",
        "style": "style_tags",
        "style_tags": "style_tags",
        "avoid": "restrictions",
        "restrictions": "restrictions",
    }
    normalized: dict[str, Any] = {}
    for key, value in raw.items():
        target = aliases.get(key, key)
        if target in {"colors", "materials", "scenes", "style_tags", "restrictions"}:
            normalized.setdefault(target, [])
            normalized[target].extend(_as_list(value))
        elif target not in normalized:
            normalized[target] = value

    for key in ("colors", "materials", "scenes", "style_tags", "restrictions"):
        if key in normalized:
            normalized[key] = list(dict.fromkeys(normalized[key]))

    if "thickness" in normalized:
        normalized["thickness"] = THICKNESS_ALIASES.get(
            str(normalized.get("thickness", "unknown")).strip().lower(),
            "unknown",
        )
    if "formality" in normalized:
        try:
            normalized["formality"] = int(normalized["formality"])
        except (TypeError, ValueError):
            normalized["formality"] = 3
        if not 1 <= normalized["formality"] <= 5:
            normalized["formality"] = 3
    return normalized


def normalize_operation(operation: ProposedOperation) -> ProposedOperation:
    if operation.op == "add":
        if not operation.item:
            return operation
        normalized = _normalize_field_aliases(dict(operation.item))
        normalized.setdefault("id", slugify(str(normalized.get("name", "item"))))
        normalized.setdefault("colors", [])
        normalized.setdefault("materials", [])
        normalized.setdefault("seasons", [])
        normalized.setdefault("thickness", "unknown")
        normalized.setdefault("scenes", [])
        normalized.setdefault("style_tags", [])
        normalized.setdefault("formality", 3)
        normalized.setdefault("restrictions", [])
        normalized.setdefault("notes", "")
        normalized.setdefault("inference_status", "inferred")
        return operation.model_copy(update={"item": normalized})

    if operation.op == "update":
        normalized_fields = _normalize_field_aliases(dict(operation.fields))
        return operation.model_copy(update={"fields": normalized_fields})

    return operation
