from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_sample_questions() -> None:
    response = client.get("/sample-questions")

    assert response.status_code == 200
    assert "Show trades pending validation" in response.json()


def test_agent_sample_questions() -> None:
    response = client.get("/agent/sample-questions")

    assert response.status_code == 200
    assert "Give me an operations morning summary." in response.json()


def test_agent_explains_application_without_data_query() -> None:
    response = client.post("/agent/ask", json={"question": "What is this app about?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "APP_EXPLANATION"
    assert payload["generatedSql"] is None
    assert payload["columns"] == []
    assert payload["rows"] == []
    assert "Trade Operations Management System" in payload["answer"]


def test_agent_explains_trade_concept_without_data_query() -> None:
    response = client.post("/agent/ask", json={"question": "What is a trade?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "CONCEPT_EXPLANATION"
    assert payload["generatedSql"] is None
    assert payload["rows"] == []
    assert "transaction" in payload["answer"]


def test_schema_contains_capital_markets_tables() -> None:
    response = client.get("/schema")

    assert response.status_code == 200
    table_names = {table["name"] for table in response.json()["tables"]}
    assert {"trades", "settlements", "counterparties", "books"}.issubset(table_names)
