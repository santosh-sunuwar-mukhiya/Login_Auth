from sqlmodel import SQLModel # type: ignore
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker  # type: ignore
from ..config import db_settings

engine = create_async_engine( # type: ignore
    url=db_settings.DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False}
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,  # type: ignore
    expire_on_commit=False
)

async def create_db_tables():
    async with engine.begin() as connection:
        from ..databases.models import Blog, User
        await connection.run_sync(SQLModel.metadata.create_all)

async def get_session():
    async with AsyncSessionFactory() as session:
        yield session
