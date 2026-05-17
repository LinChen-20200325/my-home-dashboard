"""Chapter 7：安全離場策略與房地合一稅防禦 — Thin wrapper（重構後）。

實作已搬遷至 ``app.ui.pages.chapter_7_exit``。
Migration step: Phase 2 #21
"""

from __future__ import annotations

from app.ui.pages.chapter_7_exit import render_chapter_7

__all__ = ["render_chapter_7"]


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(
        page_title="Ch.7 安全離場與流動性評估",
        page_icon="🚪",
        layout="wide",
    )
    render_chapter_7()
