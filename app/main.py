from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import (
    auth_router,
    documents_router,
    query_router,
    sessions_router,
)


app = FastAPI(title="ContractAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Auth"],
)

app.include_router(
    sessions_router,
    prefix="/sessions",
    tags=["Sessions"],
)

app.include_router(
    documents_router,
    prefix="/sessions",
    tags=["Documents"],
)

app.include_router(
    query_router,
    prefix="/sessions",
    tags=["Query"],
)
