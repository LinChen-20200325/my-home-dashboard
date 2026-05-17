"""個人現金流診斷 DTO（Ch.1 主要使用，Ch.10 決策雷達引用）。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CashflowSeverity(str, Enum):
    """淨現金流 / DTI 綜合健康度分級。

    順序由壞至好：DTI 死線 > 中產毒藥 > 現金流負 > 緩衝過低 > 健康。
    """

    DTI_LOCKED = "dti_locked"        # DTI > 70%，銀行核貸死線
    POISON_DEBT = "poison_debt"      # 有壞債（車貸／信貸／卡債）
    NEGATIVE = "negative"            # 淨現金流 < 0
    LOW_BUFFER = "low_buffer"        # 淨現金流 < 20,000
    HEALTHY = "healthy"              # 淨現金流 ≥ 20,000 且無壞債、DTI 合格


@dataclass(frozen=True)
class CashflowInput:
    """月度收支輸入（單位：元 NTD）。"""

    total_income_ntd: int
    living_cost_ntd: int
    bad_debt_ntd: int = 0


@dataclass(frozen=True)
class CashflowSnapshot:
    """現金流健康快照（service 計算後回傳給 UI）。"""

    net_cashflow_ntd: int
    dti: float
    has_bad_debt: bool
    severity: CashflowSeverity

    @property
    def is_healthy(self) -> bool:
        return self.severity == CashflowSeverity.HEALTHY
