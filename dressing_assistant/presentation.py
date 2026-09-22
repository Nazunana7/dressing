from __future__ import annotations

from .models import AssistantResult, WardrobeItem


def format_assistant_message(
    result: AssistantResult,
    wardrobe: list[WardrobeItem],
) -> str:
    names = {item.id: item.name for item in wardrobe}
    lines = [result.reply]
    if result.outfits:
        lines.append("")
        for index, outfit in enumerate(result.outfits, start=1):
            item_names = [names.get(item_id, "未知单品") for item_id in outfit.item_ids]
            lines.append(f"### 方案 {index}：{outfit.title}")
            lines.append(f"单品：{' + '.join(item_names)}")
            lines.append(outfit.reason)
            lines.append("")
    if result.proposed_operations:
        from .wardrobe import summarize_operations

        lines.append("")
        lines.append("**待确认修改**")
        lines.append(summarize_operations(result.proposed_operations))
    return "\n".join(lines).strip()
