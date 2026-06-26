import re

from openai import OpenAI

from app.config import get_settings
from app.services.schema_context import SCHEMA_CONTEXT
from app.services.sql_validator import validate_read_only_sql


SAMPLE_QUESTIONS = [
    "Show trades pending validation",
    "Show failed settlements this week",
    "Show P&L by book",
    "Show top 5 counterparties by exposure",
    "Show trades by instrument",
    "Show market value by portfolio",
    "Show trades booked today",
    "Show settlement status by counterparty",
]

SYSTEM_PROMPT = f"""
You are the AI Trade Operations Copilot embedded inside a Trade Operations Management System
used by middle-office and operations analysts.
Generate exactly one PostgreSQL SELECT query for the user's question.
Use only the schema below. Do not use comments, DDL, DML, or multiple statements.
Return SQL only, with no markdown and no explanation.

{SCHEMA_CONTEXT}
""".strip()


class SQLGenerator:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    def generate(self, question: str) -> tuple[str, str]:
        if self.client:
            sql = self._generate_with_openai(question)
            return validate_read_only_sql(sql), self._answer_hint(question)

        sql, hint = self._generate_demo_fallback(question)
        return validate_read_only_sql(sql), hint

    def _generate_with_openai(self, question: str) -> str:
        response = self.client.chat.completions.create(
            model=self.settings.openai_model,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
        )
        return response.choices[0].message.content or ""

    def _generate_demo_fallback(self, question: str) -> tuple[str, str]:
        q = re.sub(r"\s+", " ", question.lower()).strip()

        if "pending validation" in q or ("trade" in q and "pending" in q):
            return (
                "SELECT t.trade_id, i.symbol, c.name AS counterparty, b.name AS book, "
                "t.trade_date, t.side, t.quantity, t.notional, t.status "
                "FROM trades t "
                "JOIN instruments i ON i.id = t.instrument_id "
                "JOIN counterparties c ON c.id = t.counterparty_id "
                "JOIN books b ON b.id = t.book_id "
                "WHERE t.status = 'Pending Validation' "
                "ORDER BY t.trade_date DESC",
                "Trades currently waiting for validation.",
            )

        if "rejected" in q and "trade" in q:
            return (
                "SELECT t.trade_id, i.symbol, c.name AS counterparty, b.name AS book, "
                "t.trade_date, t.side, t.quantity, t.notional, t.status "
                "FROM trades t "
                "JOIN instruments i ON i.id = t.instrument_id "
                "JOIN counterparties c ON c.id = t.counterparty_id "
                "JOIN books b ON b.id = t.book_id "
                "WHERE LOWER(t.status) = 'rejected' "
                "ORDER BY t.trade_date DESC",
                "Rejected trade records.",
            )

        if "failed" in q and "settlement" in q:
            return (
                "SELECT t.trade_id, c.name AS counterparty, s.settlement_date, s.cash_amount, "
                "s.currency, s.status, s.failure_reason "
                "FROM settlements s "
                "JOIN trades t ON t.id = s.trade_id "
                "JOIN counterparties c ON c.id = s.counterparty_id "
                "WHERE s.status = 'Failed' "
                "AND s.settlement_date >= date_trunc('week', CURRENT_DATE) "
                "ORDER BY s.settlement_date DESC",
                "Failed settlements for the current week.",
            )

        if ("p&l" in q or "pnl" in q) and "book" in q:
            return (
                "SELECT b.name AS book, b.desk, ROUND(SUM(t.pnl)::numeric, 2) AS total_pnl "
                "FROM trades t "
                "JOIN books b ON b.id = t.book_id "
                "GROUP BY b.name, b.desk "
                "ORDER BY total_pnl DESC",
                "Aggregated P&L by trading book.",
            )

        if "counterpart" in q and "exposure" in q:
            return (
                "SELECT c.name AS counterparty, c.credit_rating, "
                "ROUND(SUM(ABS(t.market_value))::numeric, 2) AS exposure "
                "FROM trades t "
                "JOIN counterparties c ON c.id = t.counterparty_id "
                "GROUP BY c.name, c.credit_rating "
                "ORDER BY exposure DESC "
                "LIMIT 5",
                "Top counterparties ranked by absolute market-value exposure.",
            )

        if "trade" in q and "instrument" in q:
            return (
                "SELECT i.symbol, i.name AS instrument, i.asset_class, COUNT(t.id) AS trade_count, "
                "ROUND(SUM(t.notional)::numeric, 2) AS total_notional "
                "FROM trades t "
                "JOIN instruments i ON i.id = t.instrument_id "
                "GROUP BY i.symbol, i.name, i.asset_class "
                "ORDER BY trade_count DESC",
                "Trade activity grouped by instrument.",
            )

        if "market value" in q and "portfolio" in q:
            return (
                "SELECT p.name AS portfolio, p.strategy, p.base_currency, "
                "ROUND(SUM(t.market_value)::numeric, 2) AS market_value "
                "FROM trades t "
                "JOIN portfolios p ON p.id = t.portfolio_id "
                "GROUP BY p.name, p.strategy, p.base_currency "
                "ORDER BY market_value DESC",
                "Market value grouped by portfolio.",
            )

        if "booked today" in q:
            return (
                "SELECT t.trade_id, i.symbol, c.name AS counterparty, b.name AS book, "
                "t.trade_date, t.notional, t.status "
                "FROM trades t "
                "JOIN instruments i ON i.id = t.instrument_id "
                "JOIN counterparties c ON c.id = t.counterparty_id "
                "JOIN books b ON b.id = t.book_id "
                "WHERE t.trade_date = CURRENT_DATE "
                "ORDER BY t.trade_id",
                "Trades booked today.",
            )

        if "settlement status" in q and "counterparty" in q:
            return (
                "SELECT c.name AS counterparty, s.status, COUNT(*) AS settlement_count, "
                "ROUND(SUM(s.cash_amount)::numeric, 2) AS cash_amount "
                "FROM settlements s "
                "JOIN counterparties c ON c.id = s.counterparty_id "
                "GROUP BY c.name, s.status "
                "ORDER BY c.name, s.status",
                "Settlement status distribution by counterparty.",
            )

        return (
            "SELECT t.trade_id, i.symbol, c.name AS counterparty, b.name AS book, "
            "p.name AS portfolio, t.trade_date, t.notional, t.market_value, t.pnl, t.status "
            "FROM trades t "
            "JOIN instruments i ON i.id = t.instrument_id "
            "JOIN counterparties c ON c.id = t.counterparty_id "
            "JOIN books b ON b.id = t.book_id "
            "JOIN portfolios p ON p.id = t.portfolio_id "
            "ORDER BY t.trade_date DESC",
            "Recent trade lifecycle records.",
        )

    def _answer_hint(self, question: str) -> str:
        lowered = question.lower()
        if "settlement" in lowered:
            return "Settlement lifecycle results."
        if "p&l" in lowered or "pnl" in lowered:
            return "P&L analytics results."
        if "counterpart" in lowered:
            return "Counterparty exposure results."
        return "Capital markets query results."
