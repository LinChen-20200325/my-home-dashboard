"""槓桿魔法服務 — M2 燃料 / 增貸 / 科目四 / 股票質押 / 合資 / 區域紅利。

整合自 5 個現有檔案的計算邏輯：
    Ch.1                  — M2 貨幣與資產計算機（5 倍槓桿 10 年對決）
    Ch.4                  — 整棟大廈價差增貸 + 科目四過水追蹤
    Ch.6                  — VIP 股票質押
    Ch.8                  — 空租準備金（地段級別）
    strategy_macro        — M2/M1B 黃金交叉四象限 + 區域紅利掃描
    strategy_syndication  — 合資無本套利 + 4 道法律防護鎖

純函式設計：嚴禁 `import streamlit`；無外部 I/O。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import NamedTuple

from app.models.constants import (
    BANK_REFINANCE_LTV,
    LOCATION_VACANCY_MONTHS_MAP,
    M2_BANK_DEPOSIT_ANNUAL_RATE,
    M2_INITIAL_CAPITAL_NTD,
    M2_LEVERAGE_MULTIPLIER,
    M2_SIMULATION_YEARS,
    STOCK_PLEDGE_ANNUAL_RATE,
    STOCK_PLEDGE_LTV,
)


# ============================================================
# A. M2 燃料：通膨槓桿模擬 + M1B / M2 黃金交叉診斷
# ============================================================
@dataclass(frozen=True)
class M2SimulationResult:
    """Ch.1 M2 計算機輸出。

    名目 vs 實質購買力對比是主要洞察；
    leverage_advantage_ntd 為房地產實質購買力扣除定存實質購買力的差額。
    """

    deposit_nominal_ntd: float
    deposit_real_ntd: float
    property_initial_value_ntd: float
    property_final_nominal_ntd: float
    equity_nominal_ntd: float
    equity_real_ntd: float
    leverage_advantage_ntd: float


def simulate_m2_decade(
    annual_inflation: float,
    *,
    initial_capital_ntd: float = M2_INITIAL_CAPITAL_NTD,
    leverage_multiplier: int = M2_LEVERAGE_MULTIPLIER,
    deposit_annual_rate: float = M2_BANK_DEPOSIT_ANNUAL_RATE,
    years: int = M2_SIMULATION_YEARS,
) -> M2SimulationResult:
    """模擬定存 vs 槓桿買房在 N 年通膨下的實質購買力。

    定存：本金以 deposit_rate 複利成長，再除以通膨因子。
    買房：自備款 × 槓桿 = 房價；房價以通膨率成長；漲幅全歸自有，
          再加上原始自備款，最後除以通膨因子取實質購買力。
    """
    purchasing_power_factor = (1 + annual_inflation) ** years

    deposit_nominal = initial_capital_ntd * (1 + deposit_annual_rate) ** years
    deposit_real = deposit_nominal / purchasing_power_factor

    property_initial = initial_capital_ntd * leverage_multiplier
    property_final = property_initial * (1 + annual_inflation) ** years
    property_appreciation = property_final - property_initial
    equity_nominal = initial_capital_ntd + property_appreciation
    equity_real = equity_nominal / purchasing_power_factor

    return M2SimulationResult(
        deposit_nominal_ntd=deposit_nominal,
        deposit_real_ntd=deposit_real,
        property_initial_value_ntd=property_initial,
        property_final_nominal_ntd=property_final,
        equity_nominal_ntd=equity_nominal,
        equity_real_ntd=equity_real,
        leverage_advantage_ntd=equity_real - deposit_real,
    )


class M2Regime(str, Enum):
    """M1B/M2 + 央行立場四象限。"""

    SURGE = "surge"             # 黃金交叉 + 寬鬆 → 資金狂潮
    DRAIN = "drain"             # 死亡交叉 + 緊縮 → 資金退潮
    TRANSITION = "transition"   # 黃金交叉 + 緊縮 → 轉折前夕
    BUILDUP = "buildup"         # 死亡交叉 + 寬鬆 → 蓄力期


@dataclass(frozen=True)
class M2RegimeVerdict:
    gap_pp: float            # M1B 年增率 − M2 年增率，單位 percentage point
    is_golden_cross: bool
    is_easing: bool
    regime: M2Regime


def diagnose_m2_regime(
    m1b_yoy_pct: float, m2_yoy_pct: float, is_easing: bool
) -> M2RegimeVerdict:
    """根據 M1B / M2 年增率差距 + 央行立場判定四象限。

    gap > 0 視為黃金交叉（熱錢往風險資產流）；gap=0 視為非黃金交叉。
    """
    gap = m1b_yoy_pct - m2_yoy_pct
    is_golden_cross = gap > 0

    if is_golden_cross and is_easing:
        regime = M2Regime.SURGE
    elif (not is_golden_cross) and (not is_easing):
        regime = M2Regime.DRAIN
    elif is_golden_cross and (not is_easing):
        regime = M2Regime.TRANSITION
    else:
        regime = M2Regime.BUILDUP

    return M2RegimeVerdict(
        gap_pp=gap,
        is_golden_cross=is_golden_cross,
        is_easing=is_easing,
        regime=regime,
    )


# ============================================================
# B. 增貸 + 科目四過水追蹤（Ch.4）
# ============================================================
@dataclass(frozen=True)
class BuildingGapResult:
    """整棟大廈價差增貸計算結果（單位：萬元）。"""

    unit_gap_wan: float
    total_max_price_wan: float
    total_target_price_wan: float
    potential_refinance_gap_wan: float


def calculate_building_gap(
    max_unit_price_wan: float,
    target_unit_price_wan: float,
    ping_size: float,
) -> BuildingGapResult:
    """(同棟最高單價 − 目標單價) × 坪數 = 潛在增貸空間（萬）。

    結果可為負（目標單價高於同棟最高 → 追高），呼叫端據此警告。
    """
    unit_gap = max_unit_price_wan - target_unit_price_wan
    return BuildingGapResult(
        unit_gap_wan=unit_gap,
        total_max_price_wan=max_unit_price_wan * ping_size,
        total_target_price_wan=target_unit_price_wan * ping_size,
        potential_refinance_gap_wan=unit_gap * ping_size,
    )


class WashStage(IntEnum):
    """科目四過水四階段。值即完成步驟數。"""

    NOT_STARTED = 0
    REFINANCED = 1
    PARKED = 2
    INSTRUMENT_HELD = 3
    WHITENED = 4


@dataclass(frozen=True)
class WashProgressVerdict:
    completed_steps: int
    stage: WashStage
    is_whitened: bool


def diagnose_wash_progress(
    steps_done: tuple[bool, bool, bool, bool],
) -> WashProgressVerdict:
    """科目四四步驟（增貸→他行定存→金融工具→滿 1 年）完成度。

    UI 端強制依序勾選（disabled 鎖鏈），服務只需 sum 即可推得階段。
    """
    completed = sum(steps_done)
    return WashProgressVerdict(
        completed_steps=completed,
        stage=WashStage(completed),
        is_whitened=completed == 4,
    )


# ============================================================
# C. 股票質押（Ch.6）+ 空租準備金（Ch.8）
# ============================================================
@dataclass(frozen=True)
class StockPledgeResult:
    pledgeable_amount_ntd: float
    annual_interest_ntd: float
    monthly_interest_ntd: float


def calculate_stock_pledge(
    market_value_ntd: float,
    *,
    ltv: float = STOCK_PLEDGE_LTV,
    annual_rate: float = STOCK_PLEDGE_ANNUAL_RATE,
) -> StockPledgeResult:
    """股票質押試算（市值 × LTV → 可借金額；利率為證券週轉金）。"""
    pledgeable = market_value_ntd * ltv
    annual_interest = pledgeable * annual_rate
    return StockPledgeResult(
        pledgeable_amount_ntd=pledgeable,
        annual_interest_ntd=annual_interest,
        monthly_interest_ntd=annual_interest / 12,
    )


@dataclass(frozen=True)
class VacancyReserveResult:
    estimated_vacancy_months: int
    emergency_fund_ntd: float


def calculate_vacancy_reserve(
    location_level: int, monthly_fixed_cost_ntd: int
) -> VacancyReserveResult:
    """地段級別 1-5 → 對應空租月數 × 每月固定支出 = 絕對防禦金。

    Raises:
        KeyError: location_level 不在 LOCATION_VACANCY_MONTHS_MAP（1-5）內。
    """
    months = LOCATION_VACANCY_MONTHS_MAP[location_level]
    return VacancyReserveResult(
        estimated_vacancy_months=months,
        emergency_fund_ntd=months * monthly_fixed_cost_ntd,
    )


# ============================================================
# D. 合資套利（strategy_syndication）+ 區域紅利（strategy_macro）
# ============================================================
@dataclass(frozen=True)
class SyndicationArbitrageResult:
    """合資無本套利公式輸出（單位：萬元）。

    淨套利 = 增貸搬出的錢 − 現金買斷成本 − 裝修費。
    """

    bank_revaluation_wan: float
    refinanced_amount_wan: float
    net_arbitrage_wan: float
    is_profitable: bool


def calculate_syndication_arbitrage(
    market_price_wan: float,
    cash_deal_price_wan: float,
    renovation_cost_wan: float,
    *,
    ltv: float = BANK_REFINANCE_LTV,
) -> SyndicationArbitrageResult:
    """合資無本套利推演：半年後鑑價回歸市價 × LTV = 可增貸金額。"""
    bank_revaluation = market_price_wan
    refinanced = bank_revaluation * ltv
    net = refinanced - cash_deal_price_wan - renovation_cost_wan
    return SyndicationArbitrageResult(
        bank_revaluation_wan=bank_revaluation,
        refinanced_amount_wan=refinanced,
        net_arbitrage_wan=net,
        is_profitable=net > 0,
    )


class SafeguardCompleteness(NamedTuple):
    """4 道合資產權法律防護鎖完成度。"""

    locks_in_place: int
    total_locks: int
    is_naked: bool   # 任一鎖缺即 True → 資金裸奔


def diagnose_syndication_safeguards(
    locks_checked: tuple[bool, ...],
) -> SafeguardCompleteness:
    """4 鎖：奇數股東 / 二順位 / 預告登記 / 退場機制。任一缺即裸奔。"""
    in_place = sum(locks_checked)
    total = len(locks_checked)
    return SafeguardCompleteness(
        locks_in_place=in_place,
        total_locks=total,
        is_naked=in_place < total,
    )


class RegionalGrade(str, Enum):
    """區域紅利強度分級（由弱至強）。"""

    ORDINARY = "ordinary"     # 0 命中 → 普通區
    POTENTIAL = "potential"   # 1 命中 → 一般潛力
    STRONG = "strong"         # 2 命中 → 強勢區
    NUCLEAR = "nuclear"       # 3 命中 → 核彈級


_REGIONAL_GRADE_BY_COUNT: tuple[RegionalGrade, ...] = (
    RegionalGrade.ORDINARY,
    RegionalGrade.POTENTIAL,
    RegionalGrade.STRONG,
    RegionalGrade.NUCLEAR,
)


@dataclass(frozen=True)
class RegionalTailwindVerdict:
    tailwind_count: int
    grade: RegionalGrade


def diagnose_regional_tailwinds(
    tailwinds_hit: tuple[bool, ...],
) -> RegionalTailwindVerdict:
    """三大紅利（軌道 / 科技園區 / 預售比價）命中數 → 評級。

    Raises:
        IndexError: tailwinds_hit 命中數超出 0-3 範圍（不應發生於正常 UI）。
    """
    n = sum(tailwinds_hit)
    return RegionalTailwindVerdict(
        tailwind_count=n,
        grade=_REGIONAL_GRADE_BY_COUNT[n],
    )
