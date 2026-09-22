from __future__ import annotations

import json
from typing import Any

from .profile import build_core_profile, build_detail_profile, should_include_detail
from .wardrobe import wardrobe_context_lines
from .models import WardrobeItem


SYSTEM_RULES = """你是“Dressing”，一个本地优先的私人穿搭助手。

你必须遵守以下规则：
1. 只推荐 WARDROBE 中真实存在的衣物，不能编造衣物、颜色、材质或单品 ID。
2. 每次普通穿搭请求优先给出 1-3 套完整方案，并说明搭配理由。
3. 用户没有提供天气或出门场合时，先询问缺失信息；信息足够时直接推荐。
4. 天气、温度和体感以用户当前对话为准，不假设实时天气。
5. 如果用户说某件衣服正在清洗、没干、不能穿，把对应 item_id 放入 temporary_exclusions，并重新推荐，不能继续使用这些单品。
6. 用户要求查看衣柜时，可以分组列出真实单品。
7. 用户要求新增、修改或删除衣物时，只生成 proposed_operations，绝对不能假装已经写入文件。写文件由应用在用户明确确认后完成。
8. 不要询问或推断用户的敏感身份信息；只使用 PROFILE 中已有的资料。
9. 用户要求调整个人资料时，说明需要到管理页手动编辑 profile.md；不要在聊天里直接改 Profile。
10. 最终输出只能是一个 JSON 对象，不要输出 Markdown 代码围栏、解释或额外文字。

输出的 JSON 结构固定为：
{
  "reply": "给用户看的完整回答",
  "intent": "recommend | list_wardrobe | edit_wardrobe | ask_clarification | chat",
  "outfits": [
    {"title": "方案名称", "item_ids": ["真实衣柜 ID"], "reason": "搭配理由"}
  ],
  "proposed_operations": [
    {
      "target": "wardrobe",
      "op": "add | update | delete",
      "item_id": null,
      "item": {},
      "fields": {},
      "reason": "为什么建议这样修改"
    }
  ],
  "temporary_exclusions": ["本轮或后续轮次暂时不能穿的衣柜 ID"],
  "session_summary": "压缩后的会话摘要，最多120字"
}
"""


def build_prompt(
    *,
    message: str,
    recent_messages: list[dict[str, str]],
    session_summary: str,
    profile_meta: dict[str, Any],
    profile_body: str,
    items: list[WardrobeItem],
    temporary_exclusions: list[str],
    last_outfit_item_ids: list[str],
) -> str:
    profile_payload = build_core_profile(profile_meta)
    if should_include_detail(message, profile_meta):
        profile_payload += "\n\n" + build_detail_profile(profile_meta, profile_body)

    context = {
        "当前用户消息": message,
        "最近对话": recent_messages[-6:],
        "会话摘要": session_summary or "无",
        "个人资料上下文": profile_payload,
        "当前临时排除": temporary_exclusions,
        "上一轮推荐单品 ID": last_outfit_item_ids,
        "衣柜格式": "id | 名称 | 品类 | 子类 | 颜色 | 材质 | 厚薄 | 季节 | 场景 | 正式度 | 风格 | 禁忌/备注",
        "衣柜": wardrobe_context_lines(items),
    }
    return SYSTEM_RULES + "\n\n以下是本次需要处理的上下文：\n" + json.dumps(
        context, ensure_ascii=False, indent=2
    )
