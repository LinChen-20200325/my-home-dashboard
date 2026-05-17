"""Chapter 6：節稅護城河與富豪隱形槓桿 — Thin wrapper（重構後）。

實作已搬遷至 ``app.ui.pages.chapter_6_tax``。
Migration step: Phase 2 #20
"""

from __future__ import annotations

from app.ui.pages.chapter_6_tax import render_chapter_6

__all__ = ["render_chapter_6"]


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(
        page_title="Ch.6 節稅護城河與富豪隱形槓桿",
        page_icon="🛡️",
        layout="wide",
    )
    render_chapter_6()
