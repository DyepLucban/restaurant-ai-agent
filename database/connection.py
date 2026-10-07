from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config.settings import DB_URL

# # Synchronous
# connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
# engine = create_engine(DB_URL, connect_args=connect_args)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Asynchronous
async_engine = create_async_engine(DB_URL, pool_pre_ping=True)
SessionAsync = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with SessionAsync() as db:
        yield db