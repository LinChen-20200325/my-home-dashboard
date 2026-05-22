"""房貸 PMT 與攤還引擎（從 legacy app.py 抽出）。

來源：legacy app.py 第 24-73 行（pmt + amortization_schedule）。
fmt_wan 屬於格式化邏輯，留在 UI 層，不抽至 service。

純函式設計：
    - 嚴禁 `import streamlit` / `import pandas`
    - 數值運算對應 Excel PMT 公式
    - 攤還表回傳 list[AmortizationRow]，UI 自行轉 DataFrame
"""

from __future__ import annotations

from dataclasses import dataclass


# ============================================================
# PMT 月付金（本息平均攤還）
# ============================================================
def pmt(monthly_rate: float, n_periods: int, principal: float) -> float:
    """本息平均攤還月付金（對應 Excel PMT）。

    退化情境：
        n_periods ≤ 0 或 principal ≤ 0  → 回傳 0.0
        monthly_rate ≤ 0                → 等本金分期，principal / n_periods

    Args:
        monthly_rate: 月利率（例如年利率 2% → 0.02 / 12）
        n_periods:    總期數（月）
        principal:    本金（元）

    Returns:
        每月應繳金額（元）。
    """
    if n_periods <= 0 or principal <= 0:
        return 0.0
    if monthly_rate <= 0:
        return principal / n_periods
    factor = (1 + monthly_rate) ** n_periods
    return principal * monthly_rate * factor / (factor - 1)


def monthly_payment_from_annual(
    annual_rate: float, years: int, principal: float
) -> float:
    """方便函式：年利率 + 年期 → 月付金。

    內部呼叫 pmt(annual_rate / 12, years * 12, principal)。
    """
    return pmt(annual_rate / 12, years * 12, principal)


# ============================================================
# 房價反推 / 月付推估（Ch.1 房貸試算）
# ============================================================
def monthly_payment_for_property(
    property_price_ntd: float,
    annual_rate: float,
    years: int,
    ltv_ratio: float,
) -> float:
    """給定房屋總價、利率、年限、貸款成數，回傳月付金（本息平均攤還）。

    Args:
        property_price_ntd: 房屋總價（元）
        annual_rate:        年利率（小數，例 0.02 = 2%）
        years:              貸款年期
        ltv_ratio:          貸款成數（小數，例 0.80 = 80%）

    Returns:
        每月應繳金額（元）；退化情境（房價 / 年限 / 成數 ≤ 0）回 0.0。

    注意：本函式不含寬限期；如需逐期含寬限，請呼叫 ``amortization_schedule``。
    """
    principal = property_price_ntd * ltv_ratio
    return monthly_payment_from_annual(annual_rate, years, principal)


def max_affordable_property_price(
    available_monthly_ntd: float,
    annual_rate: float,
    years: int,
    ltv_ratio: float,
) -> float:
    """以可承擔的月付金反推最大可買房屋總價（PMT 反推）。

    公式（PMT 倒推本金）：
        principal = PMT × (factor - 1) / (r × factor)
            其中 factor = (1 + r)^n, r = annual_rate / 12, n = years × 12
        房價 = principal / ltv_ratio

    退化情境：
        available_monthly ≤ 0 或 years ≤ 0 或 ltv_ratio ≤ 0 → 0.0
        annual_rate ≤ 0 → principal = available × n（線性退化）

    Args:
        available_monthly_ntd: 扣除其他負債後，可用來繳房貸的月金額（元）
        annual_rate:           年利率（小數）
        years:                 貸款年期
        ltv_ratio:             貸款成數（小數）

    Returns:
        最大可買房屋總價（元）。
    """
    if available_monthly_ntd <= 0 or years <= 0 or ltv_ratio <= 0:
        return 0.0
    monthly_rate = annual_rate / 12
    n = years * 12
    if monthly_rate <= 0:
        principal = available_monthly_ntd * n
    else:
        factor = (1 + monthly_rate) ** n
        principal = available_monthly_ntd * (factor - 1) / (monthly_rate * factor)
    return principal / ltv_ratio


# ============================================================
# 攤還表（含寬限期）
# ============================================================
@dataclass(frozen=True)
class AmortizationRow:
    """逐月攤還表單一列。

    寬限期間 principal_paid == 0、interest 以原始本金計算；
    寬限期後本息平均攤還、剩餘本金每月遞減至 0。
    """

    period: int           # 1-indexed 月數
    year: int             # 1-indexed 年度
    payment: float
    interest: float
    principal_paid: float
    remaining_balance: float


def amortization_schedule(
    principal: float,
    annual_rate: float,
    years: int,
    grace_years: int = 0,
) -> list[AmortizationRow]:
    """逐月攤還表 — 寬限期內只繳息，之後本息平均攤還。

    Args:
        principal:    貸款本金（元）
        annual_rate:  年利率（小數，例如 0.02 = 2%）
        years:        總年期
        grace_years:  寬限期年數（內部以 min(grace_years, years) clamp）

    Returns:
        list[AmortizationRow]，長度為 years × 12。

    Raises:
        ValueError: years < 0 或 principal < 0（明顯誤用）。
    """
    if years < 0 or principal < 0:
        raise ValueError(
            f"years and principal must be non-negative; "
            f"got years={years}, principal={principal}"
        )

    monthly_rate = annual_rate / 12
    total_m = int(years * 12)
    grace_m = int(min(grace_years, years) * 12)
    pay_m = total_m - grace_m

    grace_pay = principal * monthly_rate
    post_pay = pmt(monthly_rate, pay_m, principal) if pay_m > 0 else 0.0

    rows: list[AmortizationRow] = []
    balance = principal
    for m in range(1, total_m + 1):
        if m <= grace_m:
            payment = grace_pay
            interest = principal * monthly_rate
            principal_paid = 0.0
        else:
            payment = post_pay
            interest = balance * monthly_rate
            principal_paid = payment - interest
            balance = max(balance - principal_paid, 0.0)
        rows.append(
            AmortizationRow(
                period=m,
                year=(m - 1) // 12 + 1,
                payment=payment,
                interest=interest,
                principal_paid=principal_paid,
                remaining_balance=balance,
            )
        )
    return rows
