"""Unit tests — app.services.tax（裝潢抵稅白名單分類）。"""

from __future__ import annotations

import pytest

from app.services.tax import (
    FORBIDDEN_RENOVATION_ITEMS,
    RENOVATION_OPTIONS,
    RenovationVerdict,
    classify_renovation_items,
)


pytestmark = [pytest.mark.services]


class TestClassifyRenovationItems:
    def test_empty_selection(self) -> None:
        v = classify_renovation_items(())
        assert v.allowed_items == ()
        assert v.forbidden_items == ()
        assert v.has_forbidden is False

    def test_all_allowed(self) -> None:
        allowed = ("泥作工程", "防水管線", "固定木作衣櫃")
        v = classify_renovation_items(allowed)
        assert v.allowed_items == allowed
        assert v.forbidden_items == ()
        assert v.has_forbidden is False

    def test_all_forbidden(self) -> None:
        forbidden = ("系統家具櫥櫃", "高級進口沙發", "窗簾與家電")
        v = classify_renovation_items(forbidden)
        assert v.allowed_items == ()
        assert v.forbidden_items == forbidden
        assert v.has_forbidden is True

    def test_mixed_preserves_order(self) -> None:
        mixed = ("泥作工程", "系統家具櫥櫃", "防水管線", "窗簾與家電")
        v = classify_renovation_items(mixed)
        assert v.allowed_items == ("泥作工程", "防水管線")
        assert v.forbidden_items == ("系統家具櫥櫃", "窗簾與家電")
        assert v.has_forbidden is True

    def test_unknown_item_lenient_pass_through(self) -> None:
        """未知項目（不在 RENOVATION_OPTIONS）採寬鬆策略，歸入 allowed。"""
        v = classify_renovation_items(("未知裝修",))
        assert v.allowed_items == ("未知裝修",)
        assert v.forbidden_items == ()
        assert v.has_forbidden is False

    def test_returns_named_tuple(self) -> None:
        assert isinstance(classify_renovation_items(()), RenovationVerdict)


class TestForbiddenSetSanity:
    def test_forbidden_is_frozenset(self) -> None:
        """frozenset 確保下游無法 .add() / .remove() 污染。"""
        assert isinstance(FORBIDDEN_RENOVATION_ITEMS, frozenset)
        with pytest.raises(AttributeError):
            FORBIDDEN_RENOVATION_ITEMS.add("駭客")  # type: ignore[attr-defined]

    def test_forbidden_subset_of_options(self) -> None:
        """禁區項目必須是已知選項的子集（內部一致性）。"""
        assert FORBIDDEN_RENOVATION_ITEMS <= set(RENOVATION_OPTIONS)

    def test_renovation_options_count_unchanged(self) -> None:
        """6 項裝潢選項 = 學長分類核心，異動需有意圖。"""
        assert len(RENOVATION_OPTIONS) == 6
        assert len(FORBIDDEN_RENOVATION_ITEMS) == 3
