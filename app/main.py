from fastapi import FastAPI

from app.api.documents import router as documents_router


app = FastAPI(title="ContractAI")


app.include_router(
    documents_router,
    prefix="/documents",
    tags=["Documents"],
)