"""
Database Connection - SQLAlchemy Async
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
load_dotenv()
import os
from pathlib import Path

# Get the path to the 'purchaseguard-ai'
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Ensure the 'data' folder exists in the root
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Create an absolute SQLite path
DB_PATH = DATA_DIR / "purchaseguard.db"
DEFAULT_DB_URL = f"sqlite+aiosqlite:///{DB_PATH}"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)




# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/purchaseguard.db")

engine = create_async_engine(DATABASE_URL, echo=False)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    """Dependency for database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    from app.models.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)