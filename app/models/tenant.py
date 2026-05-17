"""租客信用評分與租金科學定價 DTO（Ch.3 共用）。"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.constants import TENANT_CHECK_POINTS_PER_ITEM


@dataclass(frozen=True)
class CreditDefenseScore:
    """七道信用防線勾選結果。

    general_passed: 前 6 道一般題的勾選結果（依序）。
    boss_passed:    第 7 題魔王題（押金分期 / 押金優惠）。
                    任何 verdict 邏輯都應將魔王題視為一票否決。
    """

    general_passed: tuple[bool, ...]
    boss_passed: bool

    @property
    def passed_count(self) -> int:
        return sum(self.general_passed) + (1 if self.boss_passed else 0)

    @property
    def total_score(self) -> int:
        return self.passed_count * TENANT_CHECK_POINTS_PER_ITEM


@dataclass(frozen=True)
class RentalPricingInput:
    """租金科學定價公式輸入（學長：基礎租金 × 樓層 × 屋齡）。"""

    avg_rent_per_ping_ntd: float
    ping_size: float
    floor_label: str
    age_label: str
    vacancy_days: int = 0


@dataclass(frozen=True)
class RentalPricingResult:
    """租金科學定價公式輸出。"""

    base_rent_ntd: float
    floor_coef: float
    age_coef: float
    suggested_rent_ntd: float
