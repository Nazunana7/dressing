from pathlib import Path

from dressing_assistant.config import AppConfig
from dressing_assistant.models import WardrobeItem
from dressing_assistant.storage import (
    load_profile_document,
    load_wardrobe,
    render_profile_document,
    save_wardrobe,
)


def make_config(tmp_path: Path) -> AppConfig:
    return AppConfig.from_data_dir(tmp_path)


def test_profile_round_trip(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    config.ensure_layout()
    meta = {"basic": {"height_cm": 170}, "style": {"avoid": ["荧光色"]}}
    body = "这是个人备注。"
    config.profile_path.write_text(render_profile_document(meta, body), encoding="utf-8")

    loaded_meta, loaded_body = load_profile_document(config)

    assert loaded_meta["basic"]["height_cm"] == 170
    assert loaded_body == body


def test_wardrobe_round_trip_and_backup(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    config.ensure_layout()
    items = [
        WardrobeItem(
            id="top-white-shirt",
            name="白色亚麻衬衫",
            category="top",
            colors=["白色"],
            materials=["亚麻"],
            seasons=["spring", "summer"],
            thickness="light",
        )
    ]

    save_wardrobe(config, items)
    save_wardrobe(config, items)

    loaded = load_wardrobe(config)
    backups = list(config.backups_dir.glob("wardrobe.yaml.*.bak"))
    assert loaded[0].id == "top-white-shirt"
    assert len(backups) == 1
