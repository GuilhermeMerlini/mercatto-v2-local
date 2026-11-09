from fastapi import FastAPI

app = FastAPI(title="Mercatto v2")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
