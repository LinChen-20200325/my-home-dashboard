"""Ch.3 租客七道信用防線評分服務。

純函式設計：
    - 嚴禁 `import streamlit`
    - 輸入：app.models.tenant.CreditDefenseScore
    - 輸出：本模組 TenantRadarVerdict（服務層內部 DTO）
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.models.constants import (
    TENANT_CHECK_EXCELLENT_THRESHOLD,
    TENANT_CHECK_PASS_THRESHOLD,
)
from app.models.tenant import CreditDefenseScore


class TenantSeverity(str, Enum):
    """租客風險分級。由壞至好：DANGEROUS < MODERATE < EXCELLENT。"""

    DANGEROUS = "dangerous"   # 魔王題未過 或 總分 < 75 → 寧可空租
    MODERATE = "moderate"     # 75 ≤ 總分 < 90 且魔王題過關 → 需加保證人
    EXCELLENT = "excellent"   # 總分 ≥ 90 且魔王題過關 → 立刻簽約


@dataclass(frozen=True)
class TenantRadarVerdict:
    """七道防線評分結果。

    `boss_failed` 與 `below_pass_threshold` 為兩個獨立的失敗旗標，
    UI 層可據此精準說明判定原因。
    """

    severity: TenantSeverity
    boss_failed: bool
    below_pass_threshold: bool


def diagnose_tenant(score: CreditDefenseScore) -> TenantRadarVerdict:
    """根據七道防線勾選結果評定租客風險等級。

    優先序（從最壞往上判，避免漏判）：
        1. 魔王題未過 或 總分 < 75 → DANGEROUS
        2. 總分 ≥ 90 → EXCELLENT
        3. 其他 → MODERATE

    Args:
        score: 七道防線勾選結果 DTO。

    Returns:
        TenantRadarVerdict：含嚴重度、魔王題失守旗標、未達及格線旗標。
    """
    boss_failed = not score.boss_passed
    below_pass = score.total_score < TENANT_CHECK_PASS_THRESHOLD

    if boss_failed or below_pass:
        severity = TenantSeverity.DANGEROUS
    elif score.total_score >= TENANT_CHECK_EXCELLENT_THRESHOLD:
        severity = TenantSeverity.EXCELLENT
    else:
        severity = TenantSeverity.MODERATE

    return TenantRadarVerdict(
        severity=severity,
        boss_failed=boss_failed,
        below_pass_threshold=below_pass,
    )
