"""Chapter 4：貸款槓桿與科目四過水密技 — Thin wrapper（重構後）。

實作已搬遷至 ``app.ui.pages.chapter_4_refinance``。
Migration step: Phase 2 #18
"""

from __future__ import annotations

from app.ui.pages.chapter_4_refinance import render_chapter_4

__all__ = ["render_chapter_4"]


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(
        page_title="Ch.4 槓桿魔法：科目四過水 SOP",
        page_icon="🏦",
        layout="wide",
    )
    render_chapter_4()
