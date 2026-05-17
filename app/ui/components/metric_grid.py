"""共用 metric grid 元件。

整段重複的 ``cols = st.columns(N); col.metric(...)`` 模式抽出成
單一函式呼叫，UI 只要傳一個 list of dicts 即可。
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_metric_row(metrics: list[dict[str, Any]]) -> None:
    """在 N 個等寬欄位中渲染 N 個 st.metric。

    每個 dict 直接作為 ``st.metric`` 的 kwargs 傳入；
    支援的 key 包含 ``label`` / ``value`` / ``delta`` / ``delta_color`` / ``help`` 等。

    空 list 直接 no-op（不丟例外，方便條件式渲染）。

    Examples:
        >>> render_metric_row([
        ...     {"label": "總收入", "value": "80,000 元"},
        ...     {"label": "淨現金流", "value": "50,000 元",
        ...      "delta": "+62%", "delta_color": "normal"},
        ...     {"label": "DTI", "value": "50%",
        ...      "delta": "-20pp vs 70%", "delta_color": "inverse"},
        ... ])
    """
    if not metrics:
        return
    cols = st.columns(len(metrics))
    for col, metric_kwargs in zip(cols, metrics):
        with col:
            st.metric(**metric_kwargs)
