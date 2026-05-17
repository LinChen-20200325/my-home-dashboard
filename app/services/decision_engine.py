"""Ch.10 終極決策雷達服務 — 4 象限判定 + 警告旗標分離。

純函式設計：
    - 嚴禁 `import streamlit`
    - 輸入：app.models.property.{PropertySpec, PriceInfo} + red_flags
    - 輸出：本模組 DecisionEngineResult

設計重點：
    Terminal verdict（KILL_SHOT / GREEN_LIGHT / OBSERVATION）與
    orthogonal warning flags（talks_broken / hardware_penalty）分離。
    原 Ch.10 允許兩個警告同時觸發，單一 verdict 會丟失資訊；
    UI 端用 terminal 決定主面板樣式，用 flags 決定額外 warning blocks。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.models.constants import (
    BANK_REFINANCE_LTV,
    ELEVATOR_RATIO_DANGER,
    MIN_SAFE_PING,
)
from app.models.property import PriceInfo, PropertySpec, PropertyType


class TerminalDecision(str, Enum):
    """Ch.10 三段式終極判定（決定主面板樣式）。"""

    KILL_SHOT = "kill_shot"      # 一刀斃命 — 紅色面板，立即放棄
    OBSERVATION = "observation"  # 觀察區 — 藍色面板，須評估警告
    GREEN_LIGHT = "green_light"  # 綠燈進攻 — 綠色面板，蘋果案


@dataclass(frozen=True)
class DecisionEngineResult:
    """Ch.10 決策雷達輸出。

    terminal:  決定主面板樣式（KILL_SHOT / OBSERVATION / GREEN_LIGHT）
    *_flag:    orthogonal 警告旗標，UI 可獨立渲染額外 warning blocks
    *_indices: 命中的 red_flag 索引（方便 UI 列出具體項目）
    *_room_wan: 出價低於鑑價時的潛在超額增貸空間（萬）
    """

    terminal: TerminalDecision

    # 致命條件（任一觸發即 KILL_SHOT）
    has_red_flag: bool
    is_too_small: bool

    # 非致命警告（UI 顯示 WARNING block，與 terminal 並列）
    is_below_seller_bottom: bool
    is_elevator_bad: bool

    # 機會旗標
    is_below_appraisal: bool

    # 衍生 metrics（UI 直接顯示）
    elevator_ratio: float
    price_gap_wan: float
    triggered_red_flag_indices: tuple[int, ...]
    excess_loan_room_wan: float


def diagnose_property_decision(
    spec: PropertySpec,
    price: PriceInfo,
    red_flags: tuple[bool, ...],
) -> DecisionEngineResult:
    """Ch.10 四階段判定（KILL_SHOT > 警告 > GREEN_LIGHT > OBSERVATION）。

    優先序：
        1. 任一致命死穴（red_flag）或坪數 < 15 → KILL_SHOT
        2. 中古屋出價 < 屋主底線 → 標記 talks_broken（非致命）
        3. 梯戶比 > 4 → 標記 hardware_penalty（非致命）
        4. 全乾淨 + 出價 < 鑑價 → GREEN_LIGHT
        5. 其他 → OBSERVATION

    預售屋自動跳過屋主底線檢核（概念不適用）。

    Args:
        spec: 房屋規格 DTO。
        price: 價格情報 DTO（含屋主底線，僅中古屋使用）。
        red_flags: 致命死穴勾選結果（任意長度，依 UI 列表順序）。
    """
    elevator_ratio = spec.elevator_ratio
    has_red_flag = any(red_flags)
    is_too_small = spec.total_ping < MIN_SAFE_PING
    is_elevator_bad = elevator_ratio > ELEVATOR_RATIO_DANGER

    # 預售屋不適用屋主底線判定（概念上沒有舊房主）
    is_below_seller_bottom = (
        spec.property_type == PropertyType.RESALE and price.is_below_seller_bottom
    )

    is_below_appraisal = price.is_below_appraisal

    # ---------- terminal 判定 ----------
    if has_red_flag or is_too_small:
        terminal = TerminalDecision.KILL_SHOT
    elif (
        not is_below_seller_bottom
        and not is_elevator_bad
        and is_below_appraisal
    ):
        terminal = TerminalDecision.GREEN_LIGHT
    else:
        terminal = TerminalDecision.OBSERVATION

    # ---------- 衍生輸出 ----------
    triggered_indices = tuple(i for i, hit in enumerate(red_flags) if hit)
    excess_loan_room_wan = (
        max(0.0, -price.price_gap_wan) * BANK_REFINANCE_LTV
    )

    return DecisionEngineResult(
        terminal=terminal,
        has_red_flag=has_red_flag,
        is_too_small=is_too_small,
        is_below_seller_bottom=is_below_seller_bottom,
        is_elevator_bad=is_elevator_bad,
        is_below_appraisal=is_below_appraisal,
        elevator_ratio=elevator_ratio,
        price_gap_wan=price.price_gap_wan,
        triggered_red_flag_indices=triggered_indices,
        excess_loan_room_wan=excess_loan_room_wan,
    )
