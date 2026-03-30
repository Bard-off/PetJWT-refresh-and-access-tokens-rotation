from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel
import pathlib as ptl
import redis.asyncio as redis
from fastapi import FastAPI
from contextlib import asynccontextmanager, AsyncExitStack

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

BASE_DIR = ptl.Path(__file__).parent.parent

class InitDB:
    def __init__(self, url: str):
        self.engine = create_async_engine(url=url)
        self.session = async_sessionmaker(self.engine, expire_on_commit=False)
    async def get_db_client(self):
        async with self.session() as session:
            yield session

class JwtSettings(BaseModel):
    private_key_path: ptl.Path = BASE_DIR / "cert" / "private.pem"
    public_key_path: ptl.Path = BASE_DIR / "cert" / "public.pem"
    algorithm: str = "RS256"

class ServerSettings(BaseModel):
    allow_credentials: bool = True
    allow_origins: list = ["*"]
    allow_methods: list = ["*"]
    allow_headers: list = ["*"]
    host: str = "localhost"
    port: int = 8000
    reload: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra='ignore',
        env_file_encoding='utf-8'
    )

    server: ServerSettings = ServerSettings()
    jwt: JwtSettings = JwtSettings()

    redis_url: str
    db_url: str


settings = Settings()

db_helper = InitDB(settings.db_url)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        r = await stack.enter_async_context(redis.Redis.from_url(url=settings.redis_url))
        app.state.red = r
        try:
            await r.ping()
            log.info("Подключился к redis")
        except Exception as e:
            log.warning("Не подключился к redis")
        yield

