import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import QueryHistory
from app.schemas.agent import AgentAskRequest, AgentResponse
from app.schemas.query import HistoryItem, QueryRequest, QueryResponse, SchemaResponse
from app.services.answer_builder import build_answer
from app.services.intent_classifier import Intent, IntentClassifier
from app.services.query_executor import QueryExecutor
from app.services.schema_context import SCHEMA_CONTEXT, TABLES
from app.services.sql_generator import SAMPLE_QUESTIONS, SQLGenerator
from app.services.sql_validator import UnsafeQueryError
from app.services.trade_ops_agent import TRADE_OPS_SAMPLE_QUESTIONS, TradeOpsAgent
from app.services.trade_ops_client import TradeOpsClientError

logger = logging.getLogger(__name__)

router = APIRouter()
sql_generator = SQLGenerator()
query_executor = QueryExecutor()
trade_ops_agent = TradeOpsAgent()
intent_classifier = IntentClassifier()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "trade-operations-copilot"}


@router.get("/schema", response_model=SchemaResponse)
def get_schema() -> SchemaResponse:
    return SchemaResponse(tables=TABLES, schema_context=SCHEMA_CONTEXT)


@router.get("/sample-questions", response_model=list[str])
def get_sample_questions() -> list[str]:
    return SAMPLE_QUESTIONS


@router.get("/agent/sample-questions", response_model=list[str])
def get_agent_sample_questions() -> list[str]:
    return TRADE_OPS_SAMPLE_QUESTIONS


@router.post("/agent/ask", response_model=AgentResponse)
def ask_agent(payload: AgentAskRequest) -> AgentResponse:
    try:
        return trade_ops_agent.answer(payload.question)
    except TradeOpsClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Trade operations agent failed")
        raise HTTPException(status_code=500, detail="Unable to process the copilot question.") from exc


@router.post("/ask", response_model=QueryResponse)
def ask(payload: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    try:
        intent = intent_classifier.classify(payload.question)
        if intent != Intent.DATA_QUERY:
            answer = _answer_without_sql(payload.question, intent)
            _record_history(
                db=db,
                question=payload.question,
                intent=intent.value,
                generated_sql=None,
                answer=answer,
                row_count=0,
            )
            return QueryResponse(
                question=payload.question,
                intent=intent.value,
                answer=answer,
                generated_sql=None,
                columns=[],
                rows=[],
                row_count=0,
                error=None,
            )

        sql, answer_hint = sql_generator.generate(payload.question)
        columns, rows = query_executor.execute(db, sql)
        answer = build_answer(answer_hint, rows)

        _record_history(
            db=db,
            question=payload.question,
            intent=Intent.DATA_QUERY.value,
            generated_sql=sql,
            answer=answer,
            row_count=len(rows),
        )

        return QueryResponse(
            question=payload.question,
            intent=Intent.DATA_QUERY.value,
            answer=answer,
            generated_sql=sql,
            columns=columns,
            rows=rows,
            row_count=len(rows),
            error=None,
        )
    except UnsafeQueryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database query failed")
        raise HTTPException(status_code=500, detail="Database query failed.") from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Unable to process question")
        raise HTTPException(status_code=500, detail="Unable to process the question.") from exc


@router.get("/query-history", response_model=list[HistoryItem])
def query_history(db: Session = Depends(get_db)) -> list[QueryHistory]:
    statement = select(QueryHistory).order_by(QueryHistory.created_at.desc()).limit(25)
    return list(db.scalars(statement))


# Backward-compatible routes for the first version of the app and older frontend builds.
@router.post("/api/query", response_model=QueryResponse)
def legacy_query(payload: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    return ask(payload, db)


@router.get("/api/history", response_model=list[HistoryItem])
def legacy_history(db: Session = Depends(get_db)) -> list[QueryHistory]:
    return query_history(db)


def _record_history(
    db: Session,
    question: str,
    intent: str,
    generated_sql: str | None,
    answer: str,
    row_count: int,
) -> None:
    db.add(
        QueryHistory(
            question=question,
            intent=intent,
            generated_sql=generated_sql,
            answer=answer,
            row_count=row_count,
        )
    )
    db.commit()


def _answer_without_sql(question: str, intent: Intent) -> str:
    normalized = question.lower()
    if intent == Intent.APP_EXPLANATION:
        return (
            "This is a Trade Operations Management System. It helps operations analysts monitor "
            "booked and rejected trades, market data health, P&L, audit logs, operational alerts, "
            "and trade investigations. I can help explain the system or answer data questions "
            "such as 'Show today's rejected trades' or 'Which instruments have stale market data?'"
        )

    if intent == Intent.CONCEPT_EXPLANATION:
        if "p&l" in normalized or "pnl" in normalized or "profit and loss" in normalized:
            return (
                "P&L means profit and loss. In this system, unrealized P&L is calculated by "
                "comparing the trade price with the latest available market price. For BUY trades, "
                "profit increases when the market price rises. For SELL trades, profit increases "
                "when the market price falls."
            )
        if "rejected" in normalized:
            return (
                "A rejected trade is a trade that failed validation and should be reviewed by "
                "operations before it can be corrected, re-submitted, or excluded from the normal "
                "booked trade flow."
            )
        if "market data" in normalized:
            return (
                "Market data health shows whether instrument prices are fresh, stale, unavailable, "
                "or coming from a fallback source. It matters because stale prices can affect "
                "valuation, P&L, and operational monitoring."
            )
        if "audit" in normalized:
            return (
                "An audit trail is the chronological record of important events in the system. "
                "It helps analysts understand what happened to a trade, market data refresh, or "
                "operations workflow."
            )
        return (
            "I can explain trade operations concepts such as P&L, rejected trades, audit trails, "
            "settlements, and market data freshness in the context of this dashboard."
        )

    if intent == Intent.SMALL_TALK:
        return (
            "I'm the AI Trade Operations Copilot. I can explain this dashboard, clarify trade "
            "operations concepts, investigate trades, summarize P&L, and answer safe data questions."
        )

    return (
        "I can help with this Trade Operations Management System, but I need a clearer question. "
        "Try asking about the dashboard, a trade operations concept, or a specific data request."
    )
