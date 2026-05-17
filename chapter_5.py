"""Chapter 5：中古屋投資排雷與議價術 — Thin wrapper（重構後）。

實作已搬遷至 ``app.ui.pages.chapter_5_resale``。
Migration step: Phase 2 #19
"""

from __future__ import annotations

from app.ui.pages.chapter_5_resale import render_chapter_5

__all__ = ["render_chapter_5"]


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(
        page_title="Ch.5 中古屋投資排雷與議價術",
        page_icon="🏢",
        layout="wide",
    )
    render_chapter_5()
