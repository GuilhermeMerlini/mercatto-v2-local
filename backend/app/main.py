from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.db import init_db
from app.modules.users.router import router as users_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Mercatto v2", lifespan=lifespan)

app.include_router(users_router, prefix="/users", tags=["users"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
