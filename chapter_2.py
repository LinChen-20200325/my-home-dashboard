"""Chapter 2：預售屋『買就賺』策略 — Thin wrapper（重構後）。

實作已搬遷至 ``app.ui.pages.chapter_2_presale``；本檔保留為 thin wrapper，
讓 ``main.py`` 等既有呼叫端的 ``from chapter_2 import render_chapter_2`` 不必變更。

Migration step: Phase 2 #16
"""

from __future__ import annotations

from app.ui.pages.chapter_2_presale import render_chapter_2

__all__ = ["render_chapter_2"]


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(
        page_title="Ch.2 預售屋買就賺策略",
        page_icon="🏗️",
        layout="wide",
    )
    render_chapter_2()
