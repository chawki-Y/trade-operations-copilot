import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import router
from app.config import get_settings
from app.database import Base, engine

settings = get_settings()
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.environment != "test":
        try:
            Base.metadata.create_all(bind=engine)
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE query_history "
                        "ADD COLUMN IF NOT EXISTS intent VARCHAR(60) NOT NULL DEFAULT 'UNKNOWN'"
                    )
                )
                connection.execute(text("ALTER TABLE query_history ALTER COLUMN generated_sql DROP NOT NULL"))
        except SQLAlchemyError:
            logging.warning(
                "Optional copilot database initialization skipped. "
                "Agent endpoints can still use the Trade Operations API.",
            )
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
