from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

# Async Engine and Session for FastAPI
async_engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Synchronous Engine and Session for tests and background workers
sync_engine = create_engine(
    settings.sync_db_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.sync_db_url else {}
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

Base = declarative_base()

async def get_db():
    """Dependency for async FastAPI endpoints."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db():
    """Context manager / helper for sync operations."""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
