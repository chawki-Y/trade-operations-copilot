DROP TABLE IF EXISTS query_history;
DROP TABLE IF EXISTS settlements;
DROP TABLE IF EXISTS market_prices;
DROP TABLE IF EXISTS trades;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS instruments;
DROP TABLE IF EXISTS portfolios;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS counterparties;

CREATE TABLE counterparties (
    id SERIAL PRIMARY KEY,
    name VARCHAR(160) UNIQUE NOT NULL,
    country VARCHAR(80) NOT NULL,
    credit_rating VARCHAR(20) NOT NULL,
    sector VARCHAR(80) NOT NULL
);

CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) UNIQUE NOT NULL,
    desk VARCHAR(120) NOT NULL,
    region VARCHAR(80) NOT NULL
);

CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) UNIQUE NOT NULL,
    strategy VARCHAR(120) NOT NULL,
    base_currency VARCHAR(3) NOT NULL
);

CREATE TABLE instruments (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(40) UNIQUE NOT NULL,
    name VARCHAR(180) NOT NULL,
    asset_class VARCHAR(80) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    maturity_date DATE
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    role VARCHAR(80) NOT NULL,
    desk VARCHAR(120) NOT NULL
);

CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(40) UNIQUE NOT NULL,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id),
    counterparty_id INTEGER NOT NULL REFERENCES counterparties(id),
    book_id INTEGER NOT NULL REFERENCES books(id),
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id),
    booked_by_user_id INTEGER NOT NULL REFERENCES users(id),
    trade_date DATE NOT NULL,
    settlement_date DATE NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity NUMERIC(18, 2) NOT NULL,
    price NUMERIC(18, 4) NOT NULL,
    notional NUMERIC(18, 2) NOT NULL,
    market_value NUMERIC(18, 2) NOT NULL,
    pnl NUMERIC(18, 2) NOT NULL,
    status VARCHAR(40) NOT NULL
);

CREATE TABLE market_prices (
    id SERIAL PRIMARY KEY,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id),
    price_date DATE NOT NULL,
    close_price NUMERIC(18, 4) NOT NULL,
    source VARCHAR(80) NOT NULL
);

CREATE TABLE settlements (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER UNIQUE NOT NULL REFERENCES trades(id),
    counterparty_id INTEGER NOT NULL REFERENCES counterparties(id),
    settlement_date DATE NOT NULL,
    status VARCHAR(40) NOT NULL,
    cash_amount NUMERIC(18, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    failure_reason VARCHAR(180)
);

CREATE TABLE query_history (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    intent VARCHAR(60) NOT NULL DEFAULT 'UNKNOWN',
    generated_sql TEXT,
    answer TEXT NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
