"""房屋規格與價格情報 DTO（Ch.2 / Ch.5 / Ch.7 / Ch.8 / Ch.10 共用）。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PropertyType(str, Enum):
    """房屋類型枚舉。值與 UI 顯示文字一致。"""

    PRESALE = "預售屋"
    RESALE = "中古屋"


@dataclass(frozen=True)
class PropertySpec:
    """房屋基本規格 — Ch.10 決策雷達主要輸入。"""

    property_type: PropertyType
    total_ping: float
    units_per_floor: int
    elevator_count: int

    @property
    def elevator_ratio(self) -> float:
        """戶數 ÷ 電梯數；電梯數為 0 時回傳 inf 而非拋例外。"""
        if self.elevator_count <= 0:
            return float("inf")
        return self.units_per_floor / self.elevator_count


@dataclass(frozen=True)
class PriceInfo:
    """價格情報（單位：萬元 NTD）。

    seller_bottom_line_wan = 0 表示非中古屋或未提供屋主底線資訊。
    """

    bank_appraisal_wan: float
    your_offer_wan: float
    seller_bottom_line_wan: float = 0.0

    @property
    def price_gap_wan(self) -> float:
        """出價 − 鑑價（正 = 出價過高，需自備差額；負 = 有套利空間）。"""
        return self.your_offer_wan - self.bank_appraisal_wan

    @property
    def is_below_appraisal(self) -> bool:
        return self.price_gap_wan < 0

    @property
    def is_below_seller_bottom(self) -> bool:
        """出價是否低於屋主停損點。seller_bottom_line_wan=0 視為未設定。"""
        if self.seller_bottom_line_wan <= 0:
            return False
        return self.your_offer_wan < self.seller_bottom_line_wan
