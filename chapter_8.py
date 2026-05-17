"""Chapter 8：奈米級防坑與核彈策略 — Thin wrapper（重構後）。

實作已搬遷至 ``app.ui.pages.chapter_8_advanced``。
Migration step: Phase 2 #22
"""

from __future__ import annotations

from app.ui.pages.chapter_8_advanced import render_chapter_8

__all__ = ["render_chapter_8"]


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(
        page_title="Ch.8 奈米級防坑與核彈策略",
        page_icon="🔥",
        layout="wide",
    )
    render_chapter_8()
