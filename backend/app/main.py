from fastapi import FastAPI, status # linha editada manualmente (removido HTTPException sem uso)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Any
from app.core import config, db, errors
# linha editada manualmente: removido "from app.modules import registry" (sem uso; init_db já importa)


@asynccontextmanager # linha editada manualmente (lifespan movido para antes do app)
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Mercatto v2", lifespan=lifespan) # linha editada manualmente


@app.exception_handler(errors.DomainError)
def domain_error_exception_handler(_: Any, exc: errors.DomainError) -> JSONResponse:
    headers = {}
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        headers["WWW-Authenticate"] = "Bearer"
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
        headers=headers,
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
# linha editada manualmente: removido "app.lifespan = lifespan" (não tinha efeito)
