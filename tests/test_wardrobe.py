import pytest

from dressing_assistant.models import ProposedOperation, WardrobeItem
from dressing_assistant.wardrobe import apply_operation, compact_items


def test_apply_add_update_delete() -> None:
    items: list[WardrobeItem] = []
    add = ProposedOperation(
        target="wardrobe",
        op="add",
        item={
            "id": "bottom-black-pants",
            "name": "黑色西装裤",
            "category": "bottom",
            "colors": ["黑色"],
            "materials": ["西装面料"],
            "thickness": "medium",
        },
    )

    items, _ = apply_operation(items, add)
    assert items[0].name == "黑色西装裤"

    update = ProposedOperation(
        target="wardrobe",
        op="update",
        item_id="bottom-black-pants",
        fields={"fit": "直筒", "inference_status": "confirmed"},
    )
    items, _ = apply_operation(items, update)
    assert items[0].fit == "直筒"
    assert items[0].inference_status == "confirmed"

    delete = ProposedOperation(target="wardrobe", op="delete", item_id="bottom-black-pants")
    items, _ = apply_operation(items, delete)
    assert items == []


def test_add_rejects_duplicate_id() -> None:
    item = WardrobeItem(id="same", name="上衣", category="top")
    operation = ProposedOperation(
        target="wardrobe",
        op="add",
        item={"id": "same", "name": "另一件上衣", "category": "top"},
    )
    with pytest.raises(ValueError):
        apply_operation([item], operation)


def test_compact_items_omits_nothing_important() -> None:
    item = WardrobeItem(id="outer-grey", name="灰色开衫", category="outerwear")
    payload = compact_items([item])[0]
    assert payload["id"] == "outer-grey"
    assert payload["thickness"] == "unknown"


def test_normalize_add_aliases() -> None:
    from dressing_assistant.wardrobe import normalize_operation

    operation = ProposedOperation(
        target="wardrobe",
        op="add",
        item={
            "name": "白色棉质宽松长袖衬衫",
            "category": "top",
            "subcategory": "衬衫",
            "color": "白色",
            "material": "棉",
            "thickness": "未知",
            "seasons": ["spring", "autumn"],
            "scenarios": ["通勤"],
            "style": ["简约", "知性"],
            "formality": "未知",
        },
    )
    normalized = normalize_operation(operation)
    assert normalized.item["subtype"] == "衬衫"
    assert normalized.item["colors"] == ["白色"]
    assert normalized.item["materials"] == ["棉"]
    assert normalized.item["scenes"] == ["通勤"]
    assert normalized.item["style_tags"] == ["简约", "知性"]
    assert normalized.item["thickness"] == "unknown"
    assert normalized.item["formality"] == 3
