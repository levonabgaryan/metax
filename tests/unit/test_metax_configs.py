"""Unit tests for config selection details that silently break features when wrong."""

from __future__ import annotations

import pytest

import metax_configs
from metax_configs import DevConfigs


def test_dev_config_reads_bot_token_from_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    # given: the token lives only in .env (DevConfigs reads nothing else from it)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setattr(
        metax_configs, "_read_dotenv_value", lambda key: "from-dotenv" if key == "TELEGRAM_BOT_TOKEN" else None
    )

    # then: every dev process (incl. the taskiq worker that sends the crawl digest) sees it
    assert DevConfigs().telegram_bot_token == "from-dotenv"  # noqa: S105 — fake test value


def test_dev_config_exported_bot_token_wins_over_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "from-env")
    monkeypatch.setattr(metax_configs, "_read_dotenv_value", lambda _key: "from-dotenv")

    assert DevConfigs().telegram_bot_token == "from-env"  # noqa: S105 — fake test value


def test_dev_config_without_any_token_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setattr(metax_configs, "_read_dotenv_value", lambda _key: None)

    assert DevConfigs().telegram_bot_token is None
