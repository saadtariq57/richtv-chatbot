from fastapi import FastAPI

from app.api import routes
from app.db import init_db


app = FastAPI(title="RichTV Bot - Financial Assistant MVP")


@app.on_event("startup")
async def on_startup() -> None:
    # Initialize database schema (creates tables if they do not exist).
    await init_db()


app.include_router(routes.router)


@app.get("/")
async def root():
    return {"message": "RichTV Bot API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

