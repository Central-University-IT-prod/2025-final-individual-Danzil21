from contextlib import asynccontextmanager

import uvicorn
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from api.database import Base
from api.deps import DATABASE_URL
from api.routes import clients, advertisers, campaigns_router, ml_scores_router, ads_router, time_router, stats_router, \
    upload_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

app = FastAPI(title="PROD Backend 2025 Advertising Platform API", lifespan=lifespan)


api_router = APIRouter()

app.include_router(clients.router)
app.include_router(advertisers.router)
app.include_router(ml_scores_router)
app.include_router(ads_router)

app.include_router(upload_router)
app.include_router(campaigns_router)
app.include_router(stats_router)
app.include_router(time_router)

app.include_router(api_router)


engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True
)

if __name__ == "__main__":
    port = 8000
    if settings.SERVER_PORT:
        port = settings.SERVER_PORT

    uvicorn.run("main:app", host="REDACTED", port=port, reload=False)