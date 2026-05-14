from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .routes import profile, chat, tools, market, budget, auth

load_dotenv()

app = FastAPI(
    title       = "FinanceGPT API",
    description = "AI-powered personal finance coach for Indian professionals",
    version     = "2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(tools.router)
app.include_router(market.router)
app.include_router(budget.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "FinanceGPT API v2.0.0"}

@app.get("/")
def root():
    return {"message": "FinanceGPT API running", "docs": "/docs"}