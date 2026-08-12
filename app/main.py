from fastapi import FastAPI
app = FastAPI(title="UptimeGuard", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ОК"}