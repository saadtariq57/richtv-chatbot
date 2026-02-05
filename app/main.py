from fastapi import FastAPI
from app.api import routes

app = FastAPI(title="RichTV Bot - Financial Assistant MVP")

app.include_router(routes.router)

@app.get("/")
async def root():
    return {"message": "RichTV Bot API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

