from datetime import date, timedelta

import pytest

from app.services.trade_ops_agent import TradeOpsAgent


@pytest.fixture
def agent(monkeypatch) -> TradeOpsAgent:
    agent = TradeOpsAgent()
    agent.openai = None
    today = date.today()
    trades = [
        {
            "TradeId": "TODAY-REJECTED",
            "TradeDate": today.isoformat(),
            "Status": "REJECTED",
            "PnL": "0",
        },
        {
            "TradeId": "YESTERDAY-REJECTED",
            "TradeDate": (today - timedelta(days=1)).isoformat(),
            "Status": "REJECTED",
            "PnL": "0",
        },
        {
            "TradeId": "TODAY-BOOKED",
            "TradeDate": today.isoformat(),
            "Status": "BOOKED",
            "PnL": "125.50",
        },
    ]
    monkeypatch.setattr(agent.client, "get", lambda endpoint: trades)
    return agent


def test_today_rejected_trades_does_not_fall_back_to_history(agent: TradeOpsAgent) -> None:
    response = agent.answer("Show today's rejected trades")

    assert response.row_count == 1
    assert response.rows[0]["TradeId"] == "TODAY-REJECTED"
    assert "for today" in response.answer


def test_yesterday_rejected_trades_respects_requested_day(agent: TradeOpsAgent) -> None:
    response = agent.answer("Show yesterday's rejected trades")

    assert response.row_count == 1
    assert response.rows[0]["TradeId"] == "YESTERDAY-REJECTED"


def test_today_booked_trades_are_filtered(agent: TradeOpsAgent) -> None:
    response = agent.answer("Show trades booked today")

    assert response.row_count == 1
    assert response.rows[0]["TradeId"] == "TODAY-BOOKED"


def test_temporal_pnl_uses_only_booked_trades_in_scope(agent: TradeOpsAgent) -> None:
    response = agent.answer("Summarize today's P&L")

    assert response.row_count == 1
    assert "125.5000" in response.answer


@pytest.mark.parametrize("phrase", ["today", "yesterday", "this week", "this month"])
def test_supported_temporal_phrases_produce_a_scope(phrase: str) -> None:
    assert TradeOpsAgent._temporal_scope(phrase, date(2026, 6, 27)) is not None
