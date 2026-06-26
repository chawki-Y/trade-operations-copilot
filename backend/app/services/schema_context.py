from app.schemas.query import TableInfo


TABLES = [
    TableInfo(
        name="instruments",
        columns=["id", "symbol", "name", "asset_class", "currency", "maturity_date"],
        description="Tradable instruments such as bonds, swaps, FX forwards, and equities.",
    ),
    TableInfo(
        name="counterparties",
        columns=["id", "name", "country", "credit_rating", "sector"],
        description="External counterparties facing the trading desks.",
    ),
    TableInfo(
        name="books",
        columns=["id", "name", "desk", "region"],
        description="Trading books owned by desks and regions.",
    ),
    TableInfo(
        name="portfolios",
        columns=["id", "name", "strategy", "base_currency"],
        description="Portfolio groupings used for exposure and market value reporting.",
    ),
    TableInfo(
        name="users",
        columns=["id", "username", "full_name", "role", "desk"],
        description="Front-office and operations users who book or validate trades.",
    ),
    TableInfo(
        name="trades",
        columns=[
            "id",
            "trade_id",
            "instrument_id",
            "counterparty_id",
            "book_id",
            "portfolio_id",
            "booked_by_user_id",
            "trade_date",
            "settlement_date",
            "side",
            "quantity",
            "price",
            "notional",
            "market_value",
            "pnl",
            "status",
        ],
        description="Trade capture records with validation status, valuation, and P&L.",
    ),
    TableInfo(
        name="market_prices",
        columns=["id", "instrument_id", "price_date", "close_price", "source"],
        description="Daily market prices for instruments.",
    ),
    TableInfo(
        name="settlements",
        columns=[
            "id",
            "trade_id",
            "counterparty_id",
            "settlement_date",
            "status",
            "cash_amount",
            "currency",
            "failure_reason",
        ],
        description="Settlement lifecycle records for each trade.",
    ),
    TableInfo(
        name="query_history",
        columns=["id", "question", "intent", "generated_sql", "answer", "row_count", "created_at"],
        description="Audit trail of user questions, generated SQL, and result sizes.",
    ),
]

ALLOWED_TABLES = {table.name for table in TABLES}

SCHEMA_CONTEXT = """
Capital markets PostgreSQL schema:

instruments(id, symbol, name, asset_class, currency, maturity_date)
counterparties(id, name, country, credit_rating, sector)
books(id, name, desk, region)
portfolios(id, name, strategy, base_currency)
users(id, username, full_name, role, desk)
trades(id, trade_id, instrument_id, counterparty_id, book_id, portfolio_id,
       booked_by_user_id, trade_date, settlement_date, side, quantity, price,
       notional, market_value, pnl, status)
market_prices(id, instrument_id, price_date, close_price, source)
settlements(id, trade_id, counterparty_id, settlement_date, status, cash_amount,
            currency, failure_reason)
query_history(id, question, intent, generated_sql, answer, row_count, created_at)

Relationships:
- trades.instrument_id -> instruments.id
- trades.counterparty_id -> counterparties.id
- trades.book_id -> books.id
- trades.portfolio_id -> portfolios.id
- trades.booked_by_user_id -> users.id
- settlements.trade_id -> trades.id
- settlements.counterparty_id -> counterparties.id
- market_prices.instrument_id -> instruments.id

Common statuses:
- trades.status: Pending Validation, Validated, Cancelled, Amended
- settlements.status: Pending, Settled, Failed, Matched

Reporting notes:
- Exposure is usually SUM(ABS(trades.market_value)) or SUM(ABS(trades.notional)).
- P&L by book is SUM(trades.pnl) grouped by books.name.
- Market value by portfolio is SUM(trades.market_value) grouped by portfolios.name.
- "This week" means settlement_date >= date_trunc('week', CURRENT_DATE).
- "Booked today" means trade_date = CURRENT_DATE.
""".strip()
