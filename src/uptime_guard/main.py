from fastapi import FastAPI

from uptime_guard.api.v1.checklog import router as check_logs_router
from uptime_guard.api.v1.target import router as targets_router
from uptime_guard.api.v1.user import router as users_router

app = FastAPI(title="UptimeGuard", version="0.1.0")
app.include_router(targets_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(check_logs_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ОК"}
