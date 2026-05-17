"""Unit tests — app.services.mortgage（PMT 引擎 + 攤還表）。

驗證從 legacy app.py 抽出的金融計算精度。
"""

from __future__ import annotations

import pytest

from app.services.mortgage import (
    AmortizationRow,
    amortization_schedule,
    monthly_payment_from_annual,
    pmt,
)


pytestmark = [pytest.mark.services]


# ============================================================
# pmt — 月付金核心公式
# ============================================================
class TestPmt:
    def test_zero_rate_degrades_to_equal_principal(self) -> None:
        """0 利率：等本金分期，月付 = 本金 / 期數。"""
        assert pmt(0.0, 12, 100_000) == pytest.approx(100_000 / 12)

    def test_negative_rate_also_degrades(self) -> None:
        """負利率應被視為 0（無資料校驗，學長公式照原退化路徑）。"""
        assert pmt(-0.001, 12, 100_000) == pytest.approx(100_000 / 12)

    def test_zero_periods(self) -> None:
        assert pmt(0.005, 0, 1_000_000) == 0.0

    def test_zero_principal(self) -> None:
        assert pmt(0.005, 360, 0) == 0.0

    @pytest.mark.boundary
    def test_excel_pmt_parity_30y_2pct_12m(self) -> None:
        """30 年 / 2% 年利 / 1200 萬 → 月付 44,354.34（Excel PMT 對齊）。"""
        mp = monthly_payment_from_annual(0.02, 30, 12_000_000)
        assert mp == pytest.approx(44_354.34, abs=0.01)

    def test_monthly_helper_matches_explicit(self) -> None:
        """monthly_payment_from_annual 只是 pmt 的方便包裝。"""
        assert monthly_payment_from_annual(0.024, 20, 8_000_000) == pytest.approx(
            pmt(0.024 / 12, 20 * 12, 8_000_000)
        )


# ============================================================
# amortization_schedule — 攤還表
# ============================================================
class TestAmortizationSchedule:
    def test_30_year_schedule_length(self) -> None:
        rows = amortization_schedule(12_000_000, 0.02, 30)
        assert len(rows) == 360

    def test_zero_year_returns_empty(self) -> None:
        assert amortization_schedule(1_000_000, 0.02, 0) == []

    def test_sum_of_principal_paid_equals_initial(self) -> None:
        """總本金累計到分以下精度。"""
        rows = amortization_schedule(12_000_000, 0.02, 30)
        total = sum(r.principal_paid for r in rows)
        assert total == pytest.approx(12_000_000, abs=1.0)

    def test_final_balance_approximately_zero(self) -> None:
        rows = amortization_schedule(12_000_000, 0.02, 30)
        assert rows[-1].remaining_balance < 1.0

    def test_post_grace_payment_identity(self) -> None:
        """每列：利息 + 本金 == 月付金（寬限期後）。"""
        rows = amortization_schedule(12_000_000, 0.02, 30)
        for r in rows[:5]:
            assert r.interest + r.principal_paid == pytest.approx(r.payment)

    def test_grace_period_principal_locked(self) -> None:
        """寬限期內：principal_paid=0、利息恆為本金 × 月利率。"""
        rows = amortization_schedule(12_000_000, 0.02, 30, grace_years=3)
        expected_interest = 12_000_000 * (0.02 / 12)
        for r in rows[:36]:
            assert r.principal_paid == 0.0
            assert r.interest == pytest.approx(expected_interest)
            assert r.remaining_balance == 12_000_000

    def test_post_grace_starts_paying_down(self) -> None:
        """寬限期結束的下一個月開始攤本金。"""
        rows = amortization_schedule(12_000_000, 0.02, 30, grace_years=3)
        first_pay = rows[36]
        assert first_pay.principal_paid > 0
        assert first_pay.remaining_balance < 12_000_000

    def test_period_and_year_indexing(self) -> None:
        rows = amortization_schedule(12_000_000, 0.02, 30)
        assert rows[0].period == 1 and rows[0].year == 1
        assert rows[11].period == 12 and rows[11].year == 1
        assert rows[12].period == 13 and rows[12].year == 2
        assert rows[359].period == 360 and rows[359].year == 30


# ============================================================
# 邊界輸入驗證
# ============================================================
class TestInputValidation:
    @pytest.mark.boundary
    def test_negative_principal_raises_valueerror(self) -> None:
        with pytest.raises(ValueError):
            amortization_schedule(-100, 0.02, 30)

    @pytest.mark.boundary
    def test_negative_years_raises_valueerror(self) -> None:
        with pytest.raises(ValueError):
            amortization_schedule(1_000_000, 0.02, -5)


class TestAmortizationRowShape:
    def test_returns_dataclass(self) -> None:
        rows = amortization_schedule(1_000_000, 0.02, 1)
        assert all(isinstance(r, AmortizationRow) for r in rows)
        assert len(rows) == 12

    def test_dataclass_is_frozen(self) -> None:
        row = amortization_schedule(1_000_000, 0.02, 1)[0]
        with pytest.raises((AttributeError, Exception)):
            row.payment = 99999  # type: ignore[misc]
