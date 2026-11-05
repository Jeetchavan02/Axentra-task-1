from fastapi import FastAPI

app = FastAPI(title="Axentra Task 1", version="0.1.0")


@app.get("/health", tags=["monitoring"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
