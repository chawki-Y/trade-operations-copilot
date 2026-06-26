from enum import StrEnum
import re


class Intent(StrEnum):
    APP_EXPLANATION = "APP_EXPLANATION"
    CONCEPT_EXPLANATION = "CONCEPT_EXPLANATION"
    DATA_QUERY = "DATA_QUERY"
    SMALL_TALK = "SMALL_TALK"
    UNKNOWN = "UNKNOWN"


class IntentClassifier:
    def classify(self, question: str) -> Intent:
        normalized = self._normalize(question)

        if not normalized:
            return Intent.UNKNOWN

        if self._is_small_talk(normalized):
            return Intent.SMALL_TALK

        if self._is_app_explanation(normalized):
            return Intent.APP_EXPLANATION

        if self._is_data_query(normalized):
            return Intent.DATA_QUERY

        if self._is_concept_explanation(normalized):
            return Intent.CONCEPT_EXPLANATION

        return Intent.UNKNOWN

    @staticmethod
    def _normalize(question: str) -> str:
        return re.sub(r"\s+", " ", question.lower()).strip(" ?!.")

    @staticmethod
    def _is_small_talk(text: str) -> bool:
        exact_matches = {
            "hi",
            "hello",
            "hey",
            "thanks",
            "thank you",
            "who are you",
            "help",
            "what can you do",
        }
        if text in exact_matches:
            return True
        return bool(re.fullmatch(r"(hi|hello|hey)[, ]*(there)?", text))

    @staticmethod
    def _is_app_explanation(text: str) -> bool:
        patterns = [
            "what is this app",
            "what is this application",
            "what is this system",
            "how does this system work",
            "how does the system work",
            "explain the dashboard",
            "explain this dashboard",
            "what can this copilot do",
            "what does this copilot do",
            "what is the dashboard",
            "tell me about this app",
        ]
        return any(pattern in text for pattern in patterns)

    @staticmethod
    def _is_concept_explanation(text: str) -> bool:
        if text in {"trade", "trades", "p&l", "pnl", "settlement", "audit trail"}:
            return True

        concept_terms = [
            "p&l",
            "pnl",
            "profit and loss",
            "rejected trade",
            "market data health",
            "audit trail",
            "stale market data",
            "market data freshness",
            "booked trade",
            "trade",
            "trades",
            "trade lifecycle",
            "settlement",
            "middle office",
        ]
        explanation_starts = ("what is", "what are", "explain", "define", "what does")
        return text.startswith(explanation_starts) and any(term in text for term in concept_terms)

    @staticmethod
    def _is_data_query(text: str) -> bool:
        if re.search(r"\bTRD-\d{8}-\d{6}\b", text.upper()):
            return True

        if ("instrument" in text or "instruments" in text) and any(
            term in text for term in ["available", "use", "dropdown", "select", "supported"]
        ):
            return True

        action_terms = [
            "show",
            "list",
            "find",
            "which",
            "how many",
            "count",
            "summarize",
            "summary",
            "total",
            "top",
            "latest",
            "what happened",
            "investigate",
            "give me",
            "is any",
            "are any",
            "available",
        ]
        data_terms = [
            "trade",
            "trades",
            "rejected",
            "validated",
            "booked",
            "instrument",
            "instruments",
            "market data",
            "market price",
            "stale",
            "p&l",
            "pnl",
            "profit",
            "loss",
            "audit",
            "alert",
            "alerts",
            "operation",
            "operations",
            "counterparty",
            "counterparties",
            "settlement",
            "settlements",
            "exposure",
            "book",
            "portfolio",
        ]
        return any(term in text for term in action_terms) and any(term in text for term in data_terms)
