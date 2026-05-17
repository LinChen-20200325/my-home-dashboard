"""Chapter 11：看房現場實戰戰術手冊 — Thin wrapper（重構後）。

實作已搬遷至 ``app.ui.pages.chapter_11_combat``。
Migration step: Phase 2 #25
"""

from __future__ import annotations

from app.ui.pages.chapter_11_combat import render_chapter_11_combat_manual

__all__ = ["render_chapter_11_combat_manual"]


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(
        page_title="Ch.11 看房現場實戰戰術手冊",
        page_icon="⚔️",
        layout="wide",
    )
    render_chapter_11_combat_manual()
