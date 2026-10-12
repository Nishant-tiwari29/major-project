from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path

from app.core.config import settings
from app.core.database import async_engine, Base
from app.core.seed_data import seed_database
from app.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist and database is seeded
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    seed_database()
    yield
    # Shutdown
    await async_engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Advanced Intelligent Logistics & Vehicle Routing Optimizer 2.0 with first-principles DSA and AI/ML.",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Logistics Optimizer 2.0"}

# Mount frontend/dist if built (for unified deployment on Render)
dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if dist_dir.exists():
    app.mount("/assets", StaticFiles(directory=dist_dir / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # Don't intercept API routes or health
        if full_path.startswith("api/") or full_path == "health" or full_path == "docs" or full_path == "openapi.json":
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        file_path = dist_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(dist_dir / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "online",
            "docs_url": "/docs"
        }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
