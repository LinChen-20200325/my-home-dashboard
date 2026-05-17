"""Unit tests — app.services.tenant_radar（七道信用防線評分）。"""

from __future__ import annotations

import pytest

from app.models.tenant import CreditDefenseScore
from app.services.tenant_radar import (
    TenantRadarVerdict,
    TenantSeverity,
    diagnose_tenant,
)


pytestmark = [pytest.mark.services]


def _score(general_count: int, boss: bool) -> CreditDefenseScore:
    """Helper：建立 N 題通過 + 魔王是否過的 CreditDefenseScore。"""
    return CreditDefenseScore(
        general_passed=tuple([True] * general_count + [False] * (6 - general_count)),
        boss_passed=boss,
    )


class TestDiagnoseTenant:
    def test_all_passed_excellent(self) -> None:
        v = diagnose_tenant(_score(6, True))
        assert v.severity == TenantSeverity.EXCELLENT
        assert v.boss_failed is False
        assert v.below_pass_threshold is False

    def test_none_passed_dangerous_both_flags(self) -> None:
        v = diagnose_tenant(_score(0, False))
        assert v.severity == TenantSeverity.DANGEROUS
        assert v.boss_failed is True
        assert v.below_pass_threshold is True

    @pytest.mark.boundary
    def test_boss_veto_at_excellent_score(self) -> None:
        """6 題過 + 魔王未過 → 分數 90（達優質門檻），但魔王否決 → DANGEROUS。"""
        score = _score(6, False)
        assert score.total_score == 90
        v = diagnose_tenant(score)
        assert v.severity == TenantSeverity.DANGEROUS
        assert v.boss_failed is True
        assert v.below_pass_threshold is False  # 分數本身合格

    @pytest.mark.boundary
    def test_excellent_boundary_at_90(self) -> None:
        """5 題過 + 魔王過 = 90 分剛好踩優質線。"""
        score = _score(5, True)
        assert score.total_score == 90
        assert diagnose_tenant(score).severity == TenantSeverity.EXCELLENT

    @pytest.mark.boundary
    def test_boss_veto_at_pass_threshold(self) -> None:
        """5 題過 + 魔王未過 = 75 分（剛好及格門檻），魔王否決 → DANGEROUS。"""
        score = _score(5, False)
        assert score.total_score == 75
        v = diagnose_tenant(score)
        assert v.severity == TenantSeverity.DANGEROUS
        assert v.boss_failed is True
        assert v.below_pass_threshold is False  # 75 NOT below 75

    @pytest.mark.boundary
    def test_moderate_boundary_at_75(self) -> None:
        """4 題過 + 魔王過 = 75 分剛好踩及格線。"""
        score = _score(4, True)
        assert score.total_score == 75
        assert diagnose_tenant(score).severity == TenantSeverity.MODERATE

    def test_below_pass_threshold(self) -> None:
        """3 題過 + 魔王過 = 60 分（不及格）→ DANGEROUS。"""
        score = _score(3, True)
        assert score.total_score == 60
        v = diagnose_tenant(score)
        assert v.severity == TenantSeverity.DANGEROUS
        assert v.boss_failed is False  # 魔王過
        assert v.below_pass_threshold is True

    def test_returns_verdict(self) -> None:
        assert isinstance(diagnose_tenant(_score(6, True)), TenantRadarVerdict)
