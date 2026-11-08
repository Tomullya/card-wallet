from fastapi import FastAPI

from app.errors import register_error_handlers
from app.routers import accounts, auth, cards, health, payments

API_PREFIX = "/api/v1"

app = FastAPI(title="Mini Card Wallet API", version="1.0.0", docs_url="/docs")
register_error_handlers(app)

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(accounts.router, prefix=API_PREFIX)
app.include_router(cards.router, prefix=API_PREFIX)
app.include_router(payments.router, prefix=API_PREFIX)
