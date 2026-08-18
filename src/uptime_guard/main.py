import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from uptime_guard.api.v1.checklog import router as check_logs_router
from uptime_guard.api.v1.target import router as targets_router
from uptime_guard.api.v1.user import router as users_router
from uptime_guard.services.checker import CheckerService

checker_service = CheckerService()

@asynccontextmanager
async def lifespan(app:FastAPI):
    task = asyncio.create_task(checker_service.start())
    print("Service started")

    yield

    await checker_service.stop()
    await task
    print("Service stopped")

app = FastAPI(title="UptimeGuard", version="0.1.0", lifespan=lifespan)
app.include_router(targets_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(check_logs_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ОК"}
