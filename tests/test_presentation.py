from dressing_assistant.models import AssistantResult, OutfitProposal, WardrobeItem
from dressing_assistant.presentation import format_assistant_message


def test_outfit_rendering_uses_chinese_item_names() -> None:
    result = AssistantResult(
        reply="给你三套方案。",
        intent="recommend",
        outfits=[
            OutfitProposal(
                title="通勤",
                item_ids=["top1", "bottom1"],
                reason="颜色协调。",
            )
        ],
    )
    items = [
        WardrobeItem(id="top1", name="白色衬衫", category="top"),
        WardrobeItem(id="bottom1", name="黑色西装裤", category="bottom"),
    ]
    rendered = format_assistant_message(result, items)
    assert "白色衬衫 + 黑色西装裤" in rendered
    assert "top1" not in rendered
    assert "bottom1" not in rendered
