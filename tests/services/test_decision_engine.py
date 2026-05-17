"""Unit tests — app.services.decision_engine（Ch.10 四象限終極判定）。"""

from __future__ import annotations

import pytest

from app.models.property import PriceInfo, PropertySpec, PropertyType
from app.services.decision_engine import (
    DecisionEngineResult,
    TerminalDecision,
    diagnose_property_decision,
)


pytestmark = [pytest.mark.services]


# ============================================================
# 共用 fixtures
# ============================================================
@pytest.fixture
def clean_resale() -> PropertySpec:
    """乾淨中古屋規格：25 坪、4 戶 2 梯（ratio=2.0，HEALTHY）。"""
    return PropertySpec(PropertyType.RESALE, 25.0, 4, 2)


@pytest.fixture
def clean_presale() -> PropertySpec:
    return PropertySpec(PropertyType.PRESALE, 25.0, 4, 2)


@pytest.fixture
def good_price() -> PriceInfo:
    """offer 1800 < appraisal 2000，且 ≥ seller_bottom 1700。"""
    return PriceInfo(bank_appraisal_wan=2000, your_offer_wan=1800,
                     seller_bottom_line_wan=1700)


# ============================================================
# KILL_SHOT — 致命門檻
# ============================================================
class TestKillShot:
    def test_any_red_flag_triggers_kill_shot(
        self, clean_resale: PropertySpec, good_price: PriceInfo,
    ) -> None:
        verdict = diagnose_property_decision(
            clean_resale, good_price, (True, False, False, False),
        )
        assert verdict.terminal == TerminalDecision.KILL_SHOT
        assert verdict.has_red_flag is True
        assert verdict.triggered_red_flag_indices == (0,)

    def test_too_small_triggers_kill_shot(self, good_price: PriceInfo) -> None:
        """坪數 < 15 銀行不貸款，KILL_SHOT 不看價格。"""
        tiny = PropertySpec(PropertyType.RESALE, 12.0, 4, 2)
        verdict = diagnose_property_decision(tiny, good_price, (False,)*4)
        assert verdict.terminal == TerminalDecision.KILL_SHOT
        assert verdict.is_too_small is True

    def test_multi_red_flag_indices_preserved(
        self, clean_resale: PropertySpec, good_price: PriceInfo,
    ) -> None:
        verdict = diagnose_property_decision(
            clean_resale, good_price, (True, False, True, True),
        )
        assert verdict.triggered_red_flag_indices == (0, 2, 3)


# ============================================================
# Warning flags — 非致命警告（可同時觸發）
# ============================================================
class TestWarningFlags:
    def test_below_seller_bottom_resale_only(
        self, clean_resale: PropertySpec,
    ) -> None:
        """中古屋出價 < 屋主底線 → talks_broken 旗標亮起。"""
        price = PriceInfo(2000, 1700, 1900)  # offer 1700 < seller 1900
        verdict = diagnose_property_decision(clean_resale, price, (False,)*4)
        assert verdict.terminal == TerminalDecision.OBSERVATION
        assert verdict.is_below_seller_bottom is True

    def test_presale_skips_seller_bottom_check(
        self, clean_presale: PropertySpec,
    ) -> None:
        """預售屋自動跳過屋主底線概念。"""
        price = PriceInfo(2000, 1700, 1900)
        verdict = diagnose_property_decision(clean_presale, price, (False,)*4)
        assert verdict.is_below_seller_bottom is False
        assert verdict.terminal == TerminalDecision.GREEN_LIGHT

    def test_elevator_ratio_above_4_triggers_warning(
        self, good_price: PriceInfo,
    ) -> None:
        spec = PropertySpec(PropertyType.RESALE, 25.0, 12, 2)  # ratio=6
        verdict = diagnose_property_decision(spec, good_price, (False,)*4)
        assert verdict.terminal == TerminalDecision.OBSERVATION
        assert verdict.is_elevator_bad is True
        assert verdict.elevator_ratio == 6.0

    @pytest.mark.boundary
    def test_elevator_ratio_exactly_4_is_not_bad(
        self, good_price: PriceInfo,
    ) -> None:
        """嚴格 `>` 比較 — ratio==4 視為剛好過關，不觸發 bad。"""
        spec = PropertySpec(PropertyType.RESALE, 25.0, 8, 2)  # ratio=4
        verdict = diagnose_property_decision(spec, good_price, (False,)*4)
        assert verdict.elevator_ratio == 4.0
        assert verdict.is_elevator_bad is False
        # 沒踩警告就是 GREEN_LIGHT（因為 offer < appraisal）
        assert verdict.terminal == TerminalDecision.GREEN_LIGHT

    def test_both_warnings_fire_simultaneously(
        self, good_price: PriceInfo,
    ) -> None:
        """talks_broken + hardware_penalty 為正交旗標，可同時 True。"""
        spec = PropertySpec(PropertyType.RESALE, 25.0, 12, 2)  # ratio=6
        price = PriceInfo(2000, 1700, 1900)  # below seller
        verdict = diagnose_property_decision(spec, price, (False,)*4)
        assert verdict.terminal == TerminalDecision.OBSERVATION
        assert verdict.is_below_seller_bottom is True
        assert verdict.is_elevator_bad is True


# ============================================================
# GREEN_LIGHT — 蘋果案
# ============================================================
class TestGreenLight:
    def test_clean_with_offer_below_appraisal(
        self, clean_resale: PropertySpec, good_price: PriceInfo,
    ) -> None:
        verdict = diagnose_property_decision(
            clean_resale, good_price, (False,)*4,
        )
        assert verdict.terminal == TerminalDecision.GREEN_LIGHT
        assert verdict.is_below_appraisal is True
        # excess_loan_room = (2000−1800) × 0.8 = 160
        assert verdict.excess_loan_room_wan == pytest.approx(160.0)

    def test_observation_when_offer_above_appraisal(
        self, clean_resale: PropertySpec,
    ) -> None:
        """出價 > 鑑價但無致命警告 → OBSERVATION（不是 GREEN_LIGHT，因為沒套利）。"""
        price = PriceInfo(2000, 2100, 1700)  # offer ABOVE appraisal
        verdict = diagnose_property_decision(clean_resale, price, (False,)*4)
        assert verdict.terminal == TerminalDecision.OBSERVATION
        assert verdict.is_below_appraisal is False
        assert verdict.excess_loan_room_wan == 0.0


# ============================================================
# Verdict 物件本身
# ============================================================
class TestVerdictShape:
    def test_returns_decision_engine_result(
        self, clean_resale: PropertySpec, good_price: PriceInfo,
    ) -> None:
        verdict = diagnose_property_decision(
            clean_resale, good_price, (False,)*4,
        )
        assert isinstance(verdict, DecisionEngineResult)

    def test_verdict_is_frozen_dataclass(
        self, clean_resale: PropertySpec, good_price: PriceInfo,
    ) -> None:
        verdict = diagnose_property_decision(
            clean_resale, good_price, (False,)*4,
        )
        with pytest.raises((AttributeError, Exception)):
            verdict.terminal = TerminalDecision.KILL_SHOT  # type: ignore[misc]
