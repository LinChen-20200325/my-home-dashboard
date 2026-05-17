"""Chapter 10：400 題極限防坑與決策雷達 — Thin wrapper（重構後）。

實作已搬遷至 ``app.ui.pages.chapter_10_decision``。
Migration step: Phase 2 #24
"""

from __future__ import annotations

from app.ui.pages.chapter_10_decision import render_chapter_10_decision_engine

__all__ = ["render_chapter_10_decision_engine"]


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(
        page_title="Ch.10 400 題極限防坑與決策雷達",
        page_icon="🧭",
        layout="wide",
    )
    render_chapter_10_decision_engine()
