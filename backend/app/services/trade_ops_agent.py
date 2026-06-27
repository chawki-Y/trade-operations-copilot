from __future__ import annotations

from datetime import date, timedelta
import re
from typing import Any

from openai import OpenAI

from app.config import get_settings
from app.schemas.agent import AgentResponse, AgentSource
from app.services.intent_classifier import Intent, IntentClassifier
from app.services.trade_ops_client import TradeOpsClient


TRADE_OPS_SAMPLE_QUESTIONS = [
    "Give me an operations morning summary.",
    "Show me today's rejected trades.",
    "Why was trade TRD-20260625-000004 rejected?",
    "Summarize audit logs for trade TRD-20260625-000004.",
    "Is any market data stale?",
    "What happened with AAPL market price?",
    "Summarize today's P&L.",
    "Highlight operational risks.",
]


class TradeOpsAgent:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = TradeOpsClient()
        self.intent_classifier = IntentClassifier()
        self.openai = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    def answer(self, question: str) -> AgentResponse:
        intent = self.intent_classifier.classify(question)
        if intent == Intent.APP_EXPLANATION:
            return self._answer_app_explanation(question)
        if intent == Intent.CONCEPT_EXPLANATION:
            return self._answer_concept(question)
        if intent == Intent.SMALL_TALK:
            return self._answer_small_talk(question)
        if intent == Intent.UNKNOWN:
            return self._answer_unknown(question)

        normalized = question.lower().strip()
        trade_id = self._extract_trade_id(question)

        if trade_id and ("why" in normalized or "reject" in normalized or "investigat" in normalized):
            return self._answer_trade_investigation(question, trade_id)

        if trade_id and "audit" in normalized:
            return self._answer_trade_audit(question, trade_id)

        if ("instrument" in normalized or "instruments" in normalized) and any(
            term in normalized for term in ["available", "use", "dropdown", "select", "supported", "show", "list"]
        ):
            return self._answer_available_instruments(question)

        if "rejected" in normalized or "rejection" in normalized:
            return self._answer_rejected_trades(question)

        if "trade" in normalized and (
            any(status in normalized for status in ["booked", "validated", "new"])
            or self._temporal_scope(normalized) is not None
        ):
            return self._answer_trades(question)

        if "stale" in normalized or "market data" in normalized and "any" in normalized:
            return self._answer_market_data_health(question)

        if "market price" in normalized or "price" in normalized:
            return self._answer_market_price(question)

        if "p&l" in normalized or "pnl" in normalized:
            return self._answer_pnl(question)

        if "risk" in normalized or "summary" in normalized or "morning" in normalized or "status" in normalized:
            return self._answer_operations_summary(question)

        return self._answer_unknown(question)

    def _answer_app_explanation(self, question: str) -> AgentResponse:
        return AgentResponse(
            question=question,
            intent=Intent.APP_EXPLANATION.value,
            answer=(
                "This is a Trade Operations Management System. It helps operations analysts "
                "monitor booked and rejected trades, market data health, P&L, audit logs, "
                "operational alerts, and trade investigations. I can help explain the system "
                "or answer data questions such as 'Show today's rejected trades' or "
                "'Which instruments have stale market data?'"
            ),
            suggestions=[
                "Show today's rejected trades.",
                "What is P&L?",
                "Which instruments have stale market data?",
            ],
        )

    def _answer_concept(self, question: str) -> AgentResponse:
        normalized = question.lower()
        if "p&l" in normalized or "pnl" in normalized or "profit and loss" in normalized:
            answer = (
                "P&L means profit and loss. In this system, unrealized P&L is calculated by "
                "comparing the trade price with the latest available market price. For BUY "
                "trades, profit increases when the market price rises. For SELL trades, profit "
                "increases when the market price falls."
            )
        elif "rejected trade" in normalized or "rejected" in normalized:
            answer = (
                "A rejected trade is a trade that failed validation and was not accepted into "
                "the normal booked trade flow. In this system, rejection reasons can come from "
                "instrument validation, missing or invalid fields, or other control checks."
            )
        elif "trade" in normalized:
            answer = (
                "A trade is a transaction captured by the operations system, such as buying or "
                "selling an instrument against a counterparty. In this dashboard, each trade has "
                "an instrument, side, quantity, price, status, P&L, audit trail, and lifecycle "
                "state such as NEW, VALIDATED, BOOKED, or REJECTED."
            )
        elif "market data health" in normalized or "market data freshness" in normalized:
            answer = (
                "Market data health shows whether prices are fresh enough for operations and "
                "P&L monitoring. The system can mark prices as coming from the live API, cache, "
                "database fallback, stale data, or unavailable data."
            )
        elif "stale market data" in normalized or "stale" in normalized:
            answer = (
                "Stale market data means the latest known price is older than the freshness "
                "threshold expected by the dashboard. It can still be useful as a fallback, but "
                "operations should treat it as a risk for valuation and P&L checks."
            )
        elif "audit trail" in normalized or "audit" in normalized:
            answer = (
                "An audit trail is the timeline of operational events recorded for a trade or "
                "process. In this system it helps analysts see validations, bookings, rejections, "
                "market data events, and investigation activity."
            )
        else:
            answer = (
                "I can explain trade operations concepts such as P&L, rejected trades, audit "
                "trails, settlements, and market data freshness in the context of this dashboard."
            )

        return AgentResponse(
            question=question,
            intent=Intent.CONCEPT_EXPLANATION.value,
            answer=answer,
            suggestions=[
                "Show today's rejected trades.",
                "Explain market data health.",
                "Give me an operations morning summary.",
            ],
        )

    def _answer_small_talk(self, question: str) -> AgentResponse:
        return AgentResponse(
            question=question,
            intent=Intent.SMALL_TALK.value,
            answer=(
                "I'm the AI Trade Operations Copilot. I can explain this dashboard, clarify "
                "trade operations concepts, investigate trades, summarize P&L, and check market "
                "data or operational issues."
            ),
            suggestions=[
                "What is this app about?",
                "What is P&L?",
                "Show today's rejected trades.",
            ],
        )

    def _answer_unknown(self, question: str) -> AgentResponse:
        return AgentResponse(
            question=question,
            intent=Intent.UNKNOWN.value,
            answer=(
                "I can help with trade operations questions. For example, ask me to explain a "
                "concept like 'What is a trade?', list reference data like 'What instruments are "
                "available?', or investigate live operations data like 'Show today's rejected "
                "trades.'"
            ),
            suggestions=[
                "What is this app about?",
                "Is any market data stale?",
                "Why was trade TRD-20260625-000004 rejected?",
            ],
        )

    def _answer_available_instruments(self, question: str) -> AgentResponse:
        instruments = self.client.get("/api/instruments")
        rows = [item for item in instruments if isinstance(item, dict)]
        symbols = [str(item.get("symbol")) for item in rows if item.get("symbol")]
        asset_classes = sorted({str(item.get("asset_class")) for item in rows if item.get("asset_class")})

        if rows:
            answer = (
                f"There are {len(rows)} available instruments in the trade capture dropdown: "
                f"{', '.join(symbols)}."
            )
            if asset_classes:
                answer += f" They cover {', '.join(asset_classes)}."
        else:
            answer = "No available instruments were returned by the Trade Operations API."

        return AgentResponse(
            question=question,
            intent=Intent.DATA_QUERY.value,
            answer=answer,
            data=rows,
            columns=["symbol", "name", "asset_class", "currency"],
            rows=rows,
            row_count=len(rows),
            sources=[AgentSource(label="Instruments", endpoint="/api/instruments")],
            suggestions=[
                "Show today's rejected trades.",
                "What is a trade?",
                "What happened with AAPL market price?",
            ],
        )

    def _answer_operations_summary(self, question: str) -> AgentResponse:
        summary = self.client.get("/api/operations/summary")
        report = self.client.get("/api/trades/report")
        risks = self._build_risk_points(summary)
        answer = (
            f"Operations snapshot: {summary.get('bookedTradesToday', 0)} trades booked today, "
            f"{summary.get('rejectedTradesToday', 0)} rejected today, "
            f"total P&L today {self._money(summary.get('totalPnLToday', 0))}. "
            f"Market data shows {summary.get('staleMarketDataCount', 0)} stale and "
            f"{summary.get('unavailableMarketDataCount', 0)} unavailable instruments."
        )
        if risks:
            answer += " Key risks: " + " ".join(risks)

        return self._maybe_enhance(
            question=question,
            intent="operations_summary",
            answer=answer,
            data={"summary": summary, "report": report},
            sources=[
                AgentSource(label="Operations summary", endpoint="/api/operations/summary"),
                AgentSource(label="Trade report", endpoint="/api/trades/report"),
            ],
            suggestions=[
                "Show me today's rejected trades.",
                "Is any market data stale?",
                "Summarize today's P&L.",
            ],
        )

    def _answer_rejected_trades(self, question: str) -> AgentResponse:
        trades = self.client.get("/api/trades")
        rejected = [trade for trade in trades if trade.get("Status") == "REJECTED"]
        scope = self._temporal_scope(question)
        if scope:
            label, start_date, end_date = scope
            rejected = self._filter_trades_by_date(rejected, start_date, end_date)
        else:
            label = None

        period = f" for {label}" if label else ""
        answer = (
            f"Found {len(rejected)} rejected trade"
            f"{'s' if len(rejected) != 1 else ''}{period}."
        )
        if rejected:
            top = rejected[0]
            answer += (
                f" Latest: {top.get('TradeId')} on {top.get('Instrument')} was rejected because "
                f"{top.get('RejectionReason') or 'it failed validation'}."
            )

        return self._maybe_enhance(
            question=question,
            intent="rejected_trades",
            answer=answer,
            data=rejected,
            sources=[AgentSource(label="Trades", endpoint="/api/trades")],
            suggestions=[
                "Summarize audit logs for this trade.",
                "Give me an operations morning summary.",
            ],
        )

    def _answer_trades(self, question: str) -> AgentResponse:
        trades = [trade for trade in self.client.get("/api/trades") if isinstance(trade, dict)]
        normalized = question.lower()
        status = next(
            (
                candidate
                for candidate in ["BOOKED", "VALIDATED", "NEW"]
                if candidate.lower() in normalized
            ),
            None,
        )
        if status:
            trades = [trade for trade in trades if trade.get("Status") == status]

        scope = self._temporal_scope(normalized)
        if scope:
            label, start_date, end_date = scope
            trades = self._filter_trades_by_date(trades, start_date, end_date)
        else:
            label = None

        trade_label = f" {status.lower()}" if status else ""
        period = f" for {label}" if label else ""
        answer = f"Found {len(trades)}{trade_label} trade{'s' if len(trades) != 1 else ''}{period}."

        return self._maybe_enhance(
            question=question,
            intent="trades",
            answer=answer,
            data=trades,
            sources=[AgentSource(label="Trades", endpoint="/api/trades")],
            suggestions=["Show today's rejected trades.", "Summarize today's P&L."],
        )

    def _answer_trade_investigation(self, question: str, trade_id: str) -> AgentResponse:
        investigation = self.client.get(f"/api/operations/investigate/{trade_id}")
        trade = investigation.get("trade", {})
        audit_logs = investigation.get("auditLogs", [])
        answer = investigation.get("summary") or f"Trade {trade_id} investigation loaded."
        if trade.get("Status") == "REJECTED":
            answer += f" Rejection reason: {trade.get('RejectionReason') or 'not specified'}."
        answer += (
            f" Found {len(audit_logs)} related audit event"
            f"{'s' if len(audit_logs) != 1 else ''}."
        )

        return self._maybe_enhance(
            question=question,
            intent="trade_investigation",
            answer=answer,
            data=investigation,
            sources=[
                AgentSource(
                    label="Trade investigation",
                    endpoint=f"/api/operations/investigate/{trade_id}",
                )
            ],
            suggestions=[
                "Summarize today's P&L.",
                "Show me today's rejected trades.",
            ],
        )

    def _answer_trade_audit(self, question: str, trade_id: str) -> AgentResponse:
        investigation = self.client.get(f"/api/operations/investigate/{trade_id}")
        logs = investigation.get("auditLogs", [])
        if logs:
            answer = (
                f"Trade {trade_id} has {len(logs)} audit event"
                f"{'s' if len(logs) != 1 else ''}. Latest event: {logs[0].get('description')}."
            )
        else:
            answer = f"No audit events were found for trade {trade_id}."

        return self._maybe_enhance(
            question=question,
            intent="trade_audit",
            answer=answer,
            data=logs,
            sources=[
                AgentSource(
                    label="Trade investigation",
                    endpoint=f"/api/operations/investigate/{trade_id}",
                )
            ],
            suggestions=["Why was this trade rejected?", "Give me an operations morning summary."],
        )

    def _answer_market_data_health(self, question: str) -> AgentResponse:
        overview = self.client.get("/api/market-overview")
        stale = [
            item
            for item in overview
            if item.get("stale") or item.get("fromDatabase") or item.get("marketPrice") is None
        ]
        answer = (
            f"Market overview contains {len(stale)} stale, fallback, or unavailable "
            f"instrument{'s' if len(stale) != 1 else ''}."
        )
        if stale:
            names = ", ".join(str(item.get("symbol")) for item in stale[:5])
            answer += f" Review: {names}."

        return self._maybe_enhance(
            question=question,
            intent="market_data_health",
            answer=answer,
            data=stale,
            sources=[AgentSource(label="Market overview", endpoint="/api/market-overview")],
            suggestions=[
                "What happened with AAPL market price?",
                "Highlight operational risks.",
            ],
        )

    def _answer_market_price(self, question: str) -> AgentResponse:
        symbol = self._extract_symbol(question)
        if not symbol:
            return self._answer_market_data_health(question)

        market_data = self.client.get(f"/api/market-price/{symbol}")
        source = market_data.get("source") or "unknown"
        freshness = market_data.get("freshnessLabel") or "freshness unavailable"
        answer = (
            f"{symbol} market price is {market_data.get('marketPrice')} from {source}. "
            f"Freshness: {freshness}."
        )
        if market_data.get("fromCache"):
            answer += " The value came from the in-memory cache."
        if market_data.get("fromDatabase"):
            answer += " The value came from the database fallback."
        if market_data.get("stale"):
            answer += " The value is marked stale."

        return self._maybe_enhance(
            question=question,
            intent="market_price",
            answer=answer,
            data=market_data,
            sources=[AgentSource(label="Market price", endpoint=f"/api/market-price/{symbol}")],
            suggestions=[
                "Is any market data stale?",
                "Give me an operations morning summary.",
            ],
        )

    def _answer_pnl(self, question: str) -> AgentResponse:
        scope = self._temporal_scope(question)
        if scope:
            label, start_date, end_date = scope
            trades = [
                trade
                for trade in self.client.get("/api/trades")
                if isinstance(trade, dict) and trade.get("Status") == "BOOKED"
            ]
            trades = self._filter_trades_by_date(trades, start_date, end_date)
            total_pnl = sum(NumberHelper.to_float(trade.get("PnL")) for trade in trades)
            answer = (
                f"Booked-trade P&L for {label} is {self._money(total_pnl)} "
                f"across {len(trades)} trade{'s' if len(trades) != 1 else ''}."
            )
            return self._maybe_enhance(
                question=question,
                intent="pnl_summary",
                answer=answer,
                data=trades,
                sources=[AgentSource(label="Trades", endpoint="/api/trades")],
                suggestions=["Show today's rejected trades.", "Highlight operational risks."],
            )

        report = self.client.get("/api/trades/report")
        summary = self.client.get("/api/operations/summary")
        answer = (
            f"Total booked-trade P&L is {self._money(report.get('TotalPnL', 0))}. "
            f"Today's booked-trade P&L is {self._money(summary.get('totalPnLToday', 0))}."
        )

        return self._maybe_enhance(
            question=question,
            intent="pnl_summary",
            answer=answer,
            data={"report": report, "summary": summary},
            sources=[
                AgentSource(label="Trade report", endpoint="/api/trades/report"),
                AgentSource(label="Operations summary", endpoint="/api/operations/summary"),
            ],
            suggestions=[
                "Show me today's rejected trades.",
                "Highlight operational risks.",
            ],
        )

    def _maybe_enhance(
        self,
        question: str,
        intent: str,
        answer: str,
        data: Any,
        sources: list[AgentSource],
        suggestions: list[str],
    ) -> AgentResponse:
        if not self.openai:
            rows = self._rows_from_data(data)
            return AgentResponse(
                question=question,
                intent=Intent.DATA_QUERY.value,
                answer=answer,
                data=data,
                columns=self._columns_from_data(data),
                rows=rows,
                row_count=len(rows),
                sources=sources,
                suggestions=suggestions,
            )

        prompt = (
            "Rewrite the answer for a middle-office operations analyst. "
            "Be concise, factual, and do not invent data.\n\n"
            f"Question: {question}\n"
            f"Draft answer: {answer}\n"
            f"Data: {data}"
        )
        response = self.openai.chat.completions.create(
            model=self.settings.openai_model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the AI Trade Operations Copilot embedded inside a Trade "
                        "Operations Management System for middle-office analysts."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        enhanced = response.choices[0].message.content or answer
        tokens_used = response.usage.total_tokens if response.usage else None
        rows = self._rows_from_data(data)
        return AgentResponse(
            question=question,
            intent=Intent.DATA_QUERY.value,
            answer=enhanced,
            data=data,
            columns=self._columns_from_data(data),
            rows=rows,
            row_count=len(rows),
            sources=sources,
            suggestions=suggestions,
            model=self.settings.openai_model,
            tokens_used=tokens_used,
        )

    @staticmethod
    def _rows_from_data(data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            if isinstance(data.get("latestRejectedTrades"), list):
                return [item for item in data["latestRejectedTrades"] if isinstance(item, dict)]
            if isinstance(data.get("auditLogs"), list):
                return [item for item in data["auditLogs"] if isinstance(item, dict)]
            if isinstance(data.get("trade"), dict):
                return [data["trade"]]
            return [data]
        return []

    def _columns_from_data(self, data: Any) -> list[str]:
        rows = self._rows_from_data(data)
        if not rows:
            return []
        return list(rows[0].keys())[:8]

    @staticmethod
    def _extract_trade_id(text: str) -> str | None:
        match = re.search(r"\bTRD-\d{8}-\d{6}\b", text.upper())
        return match.group(0) if match else None

    @staticmethod
    def _extract_symbol(text: str) -> str | None:
        candidates = re.findall(r"\b[A-Z]{1,5}(?:/[A-Z]{3})?\b", text.upper())
        ignored = {"WHAT", "WHY", "SHOW", "GIVE", "TODAY", "PRICE", "MARKET", "DATA", "PNL"}
        for candidate in candidates:
            if candidate not in ignored and not candidate.startswith("TRD"):
                return candidate
        return None

    @staticmethod
    def _temporal_scope(text: str, today: date | None = None) -> tuple[str, date, date] | None:
        normalized = text.lower()
        current_date = today or date.today()

        if "yesterday" in normalized:
            start_date = current_date - timedelta(days=1)
            return "yesterday", start_date, current_date
        if "this week" in normalized:
            start_date = current_date - timedelta(days=current_date.weekday())
            return "this week", start_date, start_date + timedelta(days=7)
        if "this month" in normalized:
            start_date = current_date.replace(day=1)
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1)
            return "this month", start_date, end_date
        if "today" in normalized:
            return "today", current_date, current_date + timedelta(days=1)
        return None

    @staticmethod
    def _filter_trades_by_date(
        trades: list[dict[str, Any]],
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        filtered = []
        for trade in trades:
            raw_date = str(trade.get("TradeDate") or "")[:10]
            try:
                trade_date = date.fromisoformat(raw_date)
            except ValueError:
                continue
            if start_date <= trade_date < end_date:
                filtered.append(trade)
        return filtered

    @staticmethod
    def _money(value: Any) -> str:
        return f"{NumberHelper.to_float(value):,.4f}"

    @staticmethod
    def _build_risk_points(summary: dict[str, Any]) -> list[str]:
        risks = []
        if summary.get("rejectedTradesToday", 0) > 0:
            risks.append(f"{summary['rejectedTradesToday']} rejected trade(s) need review.")
        if summary.get("staleMarketDataCount", 0) > 0:
            risks.append(f"{summary['staleMarketDataCount']} stale market data item(s).")
        if summary.get("unavailableMarketDataCount", 0) > 0:
            risks.append(f"{summary['unavailableMarketDataCount']} unavailable market price(s).")
        if summary.get("failedMarketDataRefreshCount", 0) > 0:
            risks.append(
                f"{summary['failedMarketDataRefreshCount']} failed market refresh event(s) in 24h."
            )
        return risks


class NumberHelper:
    @staticmethod
    def to_float(value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0
