"""Argus API - Autonomous Third-Party Risk Management.

Multi-tenant FastAPI backend. Runs fully offline with deterministic heuristics;
set OPENAI_API_KEY (GPT-5.6) and Bright Data keys to enable live reasoning and
web research.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .seed import seed
from .routers import orgs, vendors, assessments, dashboard, auth, activity


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed()
    yield


app = FastAPI(
    title="Argus TPRM API",
    description="Autonomous Third-Party Risk Management - an AI crew that assesses and monitors vendors.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(orgs.router)
app.include_router(vendors.router)
app.include_router(assessments.router)
app.include_router(dashboard.router)
app.include_router(activity.router)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "llm_enabled": settings.llm_enabled,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.active_llm_model if settings.llm_enabled else None,
        "bright_data_enabled": settings.bright_data_enabled,
    }


@app.get("/")
def root():
    return {"service": "Argus TPRM", "docs": "/docs", "health": "/health"}
