from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.dependencies import query_router


app = FastAPI(title="ContractAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    documents_router,
    prefix="/documents",
    tags=["Documents"],
)

app.include_router(
    query_router,
    prefix="/documents",
    tags=["Query"],
)