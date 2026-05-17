"""Chapter 3：出租策略與滿租定價法 — Thin wrapper（重構後）。

實作已搬遷至 ``app.ui.pages.chapter_3_rental``。
Migration step: Phase 2 #17
"""

from __future__ import annotations

from app.ui.pages.chapter_3_rental import render_chapter_3

__all__ = ["render_chapter_3"]


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(
        page_title="Ch.3 租金精算與租客雷達",
        page_icon="💰",
        layout="wide",
    )
    render_chapter_3()
