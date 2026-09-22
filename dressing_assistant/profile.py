from __future__ import annotations

from typing import Any

DETAIL_KEYWORDS = {
    "脸",
    "脸型",
    "肤色",
    "颜色",
    "配色",
    "发色",
    "发型",
    "刘海",
    "痣",
    "领口",
    "项链",
    "耳环",
    "眼镜",
    "妆容",
    "气质",
    "外貌",
}


def _fmt_value(value: Any) -> str:
    if value is None or value == "":
        return "未记录"
    if isinstance(value, list):
        return "、".join(str(item) for item in value) if value else "未记录"
    if isinstance(value, dict):
        return "；".join(f"{key}: {_fmt_value(val)}" for key, val in value.items())
    return str(value)


def build_core_profile(meta: dict[str, Any]) -> str:
    """Build the compact profile that is safe to send on ordinary requests."""
    basic = meta.get("basic") or {}
    measurements = meta.get("measurements") or {}
    body = meta.get("body") or {}
    appearance = meta.get("appearance") or {}
    style = meta.get("style") or {}
    lines = [
        "【基础】",
        f"身高: {_fmt_value(basic.get('height_cm'))} cm",
        f"体重: {_fmt_value(basic.get('weight_kg'))} kg",
        f"整体气质: {_fmt_value(basic.get('presence'))}",
        "【身材与尺码】",
        f"胸围: {_fmt_value(measurements.get('bust_cm'))} cm",
        f"下胸围: {_fmt_value(measurements.get('underbust_cm'))} cm",
        f"腰围: {_fmt_value(measurements.get('waist_cm'))} cm",
        f"臀围: {_fmt_value(measurements.get('hip_cm'))} cm",
        f"肩宽: {_fmt_value(measurements.get('shoulder_width_cm'))} cm",
        f"大腿围: {_fmt_value(measurements.get('thigh_cm'))} cm",
        f"小腿围: {_fmt_value(measurements.get('calf_cm'))} cm",
        f"颈围: {_fmt_value(measurements.get('neck_cm'))} cm",
        f"腿长比例参考: 胯部至地面 {_fmt_value(measurements.get('crotch_to_floor_cm'))} cm；腰线至地面 {_fmt_value(measurements.get('waist_to_floor_cm'))} cm",
        f"体型: {_fmt_value(body.get('body_type'))}",
        f"版型偏好: {_fmt_value(body.get('fit_preference'))}",
        f"需要留意的穿着点: {_fmt_value(body.get('fit_notes'))}",
        "【颜色与风格】",
        f"肤色: {_fmt_value(appearance.get('skin_tone'))}",
        f"风格偏好: {_fmt_value(style.get('preferences'))}",
        f"避雷清单: {_fmt_value(style.get('avoid'))}",
        f"常用场景: {_fmt_value(style.get('scenes'))}",
    ]
    return "\n".join(lines)


def should_include_detail(message: str, meta: dict[str, Any]) -> bool:
    if not message:
        return False
    if any(keyword in message for keyword in DETAIL_KEYWORDS):
        return True
    # A direct appearance question should get the detailed document.
    return "长相" in message or "五官" in message


def build_detail_profile(meta: dict[str, Any], body: str) -> str:
    appearance = meta.get("appearance") or {}
    facial = meta.get("facial") or {}
    lines = [
        "【外貌细节】",
        f"肤色: {_fmt_value(appearance.get('skin_tone'))}",
        f"面部整体: {_fmt_value(appearance.get('face_summary'))}",
        f"气质: {_fmt_value(appearance.get('presence'))}",
        f"面部结构: {_fmt_value(facial.get('structure'))}",
        f"五官特征: {_fmt_value(facial.get('features'))}",
        f"辨识度: {_fmt_value(facial.get('highlight'))}",
        f"需要避免的视觉问题: {_fmt_value(facial.get('concerns'))}",
    ]
    if body.strip():
        lines.extend(["", "【个人备注】", body.strip()])
    return "\n".join(lines)
