"""房產攻略 — Composition root（重構後）。

只負責：
    1. 設定 Streamlit 頁面 metadata
    2. 委派路由給 ``app.ui.router.run()``

所有商業邏輯 / UI 渲染都在 ``app/`` 分層架構內：
    app/models/        DTO + 硬性門檻 SSOT
    app/services/      pure-function 商業邏輯（10 個服務）
    app/repositories/  外部 I/O 包裝（secrets + openai_client）
    app/ui/pages/      14 個頁面（純 Streamlit）
    app/ui/components/ 共用 verdict / metric_grid 元件
    app/ui/router.py   側邊欄 + CHAPTERS 分派

Migration step: Phase 2 #30 + #31
"""

from __future__ import annotations

import streamlit as st

from app.ui.router import run


st.set_page_config(
    page_title="房產攻略",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded",
)


run()
