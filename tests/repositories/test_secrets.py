"""Unit tests — app.repositories.secrets（API Key 雙來源解析）。

驗證點：
    - 純函式 resolve_api_key 在各種 candidate 狀態下的行為
    - read_streamlit_secret 對缺失 / 例外的容忍度
    - monkey-patch st.secrets 模擬部署環境
"""

from __future__ import annotations

import pytest

from app.repositories import secrets as secrets_mod
from app.repositories.secrets import read_streamlit_secret, resolve_api_key


pytestmark = [pytest.mark.repositories]


# ============================================================
# resolve_api_key — 雙來源優先序純函式
# ============================================================
class TestResolveApiKey:
    def test_both_sources_empty_returns_none(self) -> None:
        assert resolve_api_key(None, "NONEXISTENT_TEST_KEY") is None
        assert resolve_api_key("", "NONEXISTENT_TEST_KEY") is None

    def test_whitespace_only_candidate_returns_none(self) -> None:
        assert resolve_api_key("   ", "NONEXISTENT_TEST_KEY") is None
        assert resolve_api_key("\t\n ", "NONEXISTENT_TEST_KEY") is None

    def test_candidate_trimmed(self) -> None:
        assert resolve_api_key("sk-test", "NONEXISTENT_TEST_KEY") == "sk-test"
        assert resolve_api_key("  sk-test  ", "NONEXISTENT_TEST_KEY") == "sk-test"
        assert resolve_api_key("sk-test\n", "NONEXISTENT_TEST_KEY") == "sk-test"

    def test_secret_takes_priority_over_candidate(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """secrets 中有值時，忽略 sidebar candidate。"""
        # monkey-patch 用 dict 模擬 st.secrets
        fake_secrets = {"OPENAI_API_KEY": "sk-from-secrets"}

        class _FakeSt:
            secrets = fake_secrets

        monkeypatch.setattr(secrets_mod, "_st", _FakeSt, raising=False)
        monkeypatch.setattr(secrets_mod, "_STREAMLIT_AVAILABLE", True)

        result = resolve_api_key("sk-from-sidebar", "OPENAI_API_KEY")
        assert result == "sk-from-secrets"

    def test_falls_back_to_candidate_when_secret_missing(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class _FakeSt:
            secrets = {}  # 空的 secrets

        monkeypatch.setattr(secrets_mod, "_st", _FakeSt, raising=False)
        monkeypatch.setattr(secrets_mod, "_STREAMLIT_AVAILABLE", True)

        assert resolve_api_key("sk-fallback", "OPENAI_API_KEY") == "sk-fallback"

    def test_returns_none_when_both_missing(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class _FakeSt:
            secrets = {}

        monkeypatch.setattr(secrets_mod, "_st", _FakeSt, raising=False)
        monkeypatch.setattr(secrets_mod, "_STREAMLIT_AVAILABLE", True)

        assert resolve_api_key(None, "OPENAI_API_KEY") is None


# ============================================================
# read_streamlit_secret — st.secrets 包裝
# ============================================================
class TestReadStreamlitSecret:
    def test_returns_none_when_streamlit_unavailable(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(secrets_mod, "_STREAMLIT_AVAILABLE", False)
        assert read_streamlit_secret("ANY_KEY") is None

    def test_returns_value_when_present(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class _FakeSt:
            secrets = {"FOO": "bar"}

        monkeypatch.setattr(secrets_mod, "_st", _FakeSt, raising=False)
        monkeypatch.setattr(secrets_mod, "_STREAMLIT_AVAILABLE", True)
        assert read_streamlit_secret("FOO") == "bar"

    def test_returns_none_when_key_missing(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class _FakeSt:
            secrets = {"OTHER_KEY": "v"}

        monkeypatch.setattr(secrets_mod, "_st", _FakeSt, raising=False)
        monkeypatch.setattr(secrets_mod, "_STREAMLIT_AVAILABLE", True)
        assert read_streamlit_secret("ABSENT") is None

    def test_returns_none_when_value_empty_or_whitespace(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class _FakeSt:
            secrets = {"EMPTY": "", "WS": "   \n"}

        monkeypatch.setattr(secrets_mod, "_st", _FakeSt, raising=False)
        monkeypatch.setattr(secrets_mod, "_STREAMLIT_AVAILABLE", True)
        assert read_streamlit_secret("EMPTY") is None
        assert read_streamlit_secret("WS") is None

    def test_swallows_arbitrary_exceptions_to_none(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """secrets.toml 損毀 / SDK 內部錯誤 → 靜默 None，不丟例外。"""
        class _ExplodingSecrets:
            def __contains__(self, key: str) -> bool:
                raise RuntimeError("secrets.toml malformed")

        class _FakeSt:
            secrets = _ExplodingSecrets()

        monkeypatch.setattr(secrets_mod, "_st", _FakeSt, raising=False)
        monkeypatch.setattr(secrets_mod, "_STREAMLIT_AVAILABLE", True)
        # 不該爆，靜默回 None
        assert read_streamlit_secret("FOO") is None
