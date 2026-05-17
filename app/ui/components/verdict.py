"""共用 verdict / severity 渲染元件。

提供統一介面把『嚴重度 enum』映射到 Streamlit 的不同 alert 樣式
（st.error / st.warning / st.info / st.success / st.caption），
避免在每個頁面重複寫一長串 if/elif。

設計重點：
    - 不引入 service 層常數（避免循環依賴）
    - 接受任意 enum / hashable verdict value 作為 dict key
    - 不在 panels dict 找到對應值時靜默略過（UI 可選擇『不渲染』某些嚴重度）
"""

from __future__ import annotations

from typing import Any, Callable, Literal

import streamlit as st


PanelLevel = Literal["error", "warning", "info", "success", "caption"]


_PANEL_RENDERERS: dict[PanelLevel, Callable[[str], Any]] = {
    "error": st.error,
    "warning": st.warning,
    "info": st.info,
    "success": st.success,
    "caption": st.caption,
}


def render_panel(level: PanelLevel, message: str) -> None:
    """根據 level 字串分派到對應的 Streamlit alert 函式。

    Examples:
        >>> render_panel("error", "🚫 你完蛋了！")
        # 等同 st.error("🚫 你完蛋了！")
    """
    _PANEL_RENDERERS[level](message)


def render_verdict(
    verdict_value: Any,
    panels: dict[Any, tuple[PanelLevel, str]],
) -> None:
    """把 verdict enum 值映射到 (level, message) 並渲染對應 alert。

    在 panels dict 找不到對應 key 時**靜默略過**（不丟例外），
    讓 UI 可以選擇性對某些嚴重度不顯示主面板（例如 OBSERVATION）。

    Args:
        verdict_value: enum value 或任何 hashable 物件。
        panels: dict 把 verdict value 映射到 (panel_level, message)。

    Examples:
        >>> from app.services.cashflow import CashflowSeverity
        >>> render_verdict(snapshot.severity, {
        ...     CashflowSeverity.DTI_LOCKED: ("error", "🚫 DTI 死線..."),
        ...     CashflowSeverity.HEALTHY:    ("success", "✅ 體質健康"),
        ... })
    """
    if verdict_value in panels:
        level, message = panels[verdict_value]
        _PANEL_RENDERERS[level](message)
