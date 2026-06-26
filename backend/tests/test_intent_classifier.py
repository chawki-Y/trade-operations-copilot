import pytest

from app.services.intent_classifier import Intent, IntentClassifier


@pytest.mark.parametrize(
    ("question", "intent"),
    [
        ("What is this app about?", Intent.APP_EXPLANATION),
        ("Explain the dashboard.", Intent.APP_EXPLANATION),
        ("What is P&L?", Intent.CONCEPT_EXPLANATION),
        ("What is stale market data?", Intent.CONCEPT_EXPLANATION),
        ("What is a trade?", Intent.CONCEPT_EXPLANATION),
        ("trade", Intent.CONCEPT_EXPLANATION),
        ("What are the available instruments to use?", Intent.DATA_QUERY),
        ("Show today's rejected trades.", Intent.DATA_QUERY),
        ("What happened to trade TRD-20260625-000004?", Intent.DATA_QUERY),
        ("Hi", Intent.SMALL_TALK),
        ("Thanks", Intent.SMALL_TALK),
    ],
)
def test_classifies_supported_intents(question: str, intent: Intent) -> None:
    classifier = IntentClassifier()

    assert classifier.classify(question) == intent
