import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path
from app.config import settings
from app.database import engine, Base
from app.routers import auth, gmail, sheets, leads, templates, campaigns, inbox, pipeline, analytics, spam_test, warmup, notifications
from app.utils.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    scheduler.start()
    yield
    scheduler.stop()
    await engine.dispose()


app = FastAPI(
    title="Outreach CRM",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(gmail.router, prefix="/api/v1/gmail", tags=["Gmail"])
app.include_router(sheets.router, prefix="/api/v1/sheets", tags=["Sheets"])
app.include_router(leads.router, prefix="/api/v1/leads", tags=["Leads"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(campaigns.router, prefix="/api/v1/campaigns", tags=["Campaigns"])
app.include_router(inbox.router, prefix="/api/v1/inbox", tags=["Inbox"])
app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(spam_test.router, prefix="/api/v1/spam-test", tags=["Spam Test"])
app.include_router(warmup.router, prefix="/api/v1/warmup", tags=["Warmup"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])

static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.ENVIRONMENT == "development")
