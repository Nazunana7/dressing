from __future__ import annotations

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .config import AppConfig
from .models import WardrobeItem

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def ensure_layout(config: AppConfig) -> None:
    config.ensure_layout()


def backup_file(path: Path, backups_dir: Path) -> Path | None:
    if not path.exists():
        return None
    backups_dir.mkdir(parents=True, exist_ok=True)
    target = backups_dir / f"{path.name}.{_timestamp()}.bak"
    shutil.copy2(path, target)
    _trim_backups(backups_dir, path.name, keep=20)
    return target


def _trim_backups(backups_dir: Path, stem: str, keep: int) -> None:
    matches = sorted(backups_dir.glob(f"{stem}.*.bak"), key=lambda p: p.stat().st_mtime)
    for old in matches[:-keep]:
        old.unlink(missing_ok=True)


def atomic_write_text(path: Path, text: str, backups_dir: Path | None = None) -> None:
    if backups_dir is not None:
        backup_file(path, backups_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(f"{path.name} 顶层必须是映射结构")
    return loaded


def dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=1000,
    )


def load_profile_document(config: AppConfig) -> tuple[dict[str, Any], str]:
    if not config.profile_path.exists():
        return {}, ""
    text = config.profile_path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw_meta, body = match.groups()
    meta = yaml.safe_load(raw_meta) or {}
    if not isinstance(meta, dict):
        raise ValueError("profile.md front matter 必须是映射结构")
    return meta, body.strip()


def render_profile_document(meta: dict[str, Any], body: str) -> str:
    return f"---\n{dump_yaml(meta).strip()}\n---\n\n{body.strip()}\n"


def load_wardrobe(config: AppConfig) -> list[WardrobeItem]:
    raw = load_yaml(config.wardrobe_path)
    items = raw.get("items") or []
    if not isinstance(items, list):
        raise ValueError("wardrobe.yaml 的 items 必须是列表")
    return [WardrobeItem.model_validate(item) for item in items]


def save_wardrobe(config: AppConfig, items: list[WardrobeItem]) -> None:
    payload = {
        "version": 1,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "items": [item.model_dump(mode="python") for item in items],
    }
    atomic_write_text(
        config.wardrobe_path,
        dump_yaml(payload),
        backups_dir=config.backups_dir,
    )
