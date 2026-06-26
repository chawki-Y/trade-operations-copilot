from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Counterparty(Base):
    __tablename__ = "counterparties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    credit_rating: Mapped[str] = mapped_column(String(20), nullable=False)
    sector: Mapped[str] = mapped_column(String(80), nullable=False)

    trades: Mapped[list["Trade"]] = relationship(back_populates="counterparty")
    settlements: Mapped[list["Settlement"]] = relationship(back_populates="counterparty")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    desk: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str] = mapped_column(String(80), nullable=False)

    trades: Mapped[list["Trade"]] = relationship(back_populates="book")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    strategy: Mapped[str] = mapped_column(String(120), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)

    trades: Mapped[list["Trade"]] = relationship(back_populates="portfolio")


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(80), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    maturity_date: Mapped[date | None] = mapped_column(Date)

    trades: Mapped[list["Trade"]] = relationship(back_populates="instrument")
    market_prices: Mapped[list["MarketPrice"]] = relationship(back_populates="instrument")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(80), nullable=False)
    desk: Mapped[str] = mapped_column(String(120), nullable=False)

    trades: Mapped[list["Trade"]] = relationship(back_populates="booked_by_user")


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    counterparty_id: Mapped[int] = mapped_column(ForeignKey("counterparties.id"), nullable=False)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), nullable=False)
    booked_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    settlement_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    notional: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    market_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    pnl: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)

    instrument: Mapped[Instrument] = relationship(back_populates="trades")
    counterparty: Mapped[Counterparty] = relationship(back_populates="trades")
    book: Mapped[Book] = relationship(back_populates="trades")
    portfolio: Mapped[Portfolio] = relationship(back_populates="trades")
    booked_by_user: Mapped[User] = relationship(back_populates="trades")
    settlement: Mapped["Settlement"] = relationship(back_populates="trade", uselist=False)


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    price_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    close_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)

    instrument: Mapped[Instrument] = relationship(back_populates="market_prices")


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_id: Mapped[int] = mapped_column(ForeignKey("trades.id"), unique=True, nullable=False)
    counterparty_id: Mapped[int] = mapped_column(ForeignKey("counterparties.id"), nullable=False)
    settlement_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    cash_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(180))

    trade: Mapped[Trade] = relationship(back_populates="settlement")
    counterparty: Mapped[Counterparty] = relationship(back_populates="settlements")


class QueryHistory(Base):
    __tablename__ = "query_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(String(60), nullable=False, default="UNKNOWN")
    generated_sql: Mapped[str | None] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
