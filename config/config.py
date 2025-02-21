from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()


class DBConfig(BaseSettings):
    DATABASE_URL: str


class RedisConifg(BaseSettings):
    host: str
    port: int


class RMQConifg(BaseSettings):
    rmq_url: str

db_config = DBConfig(
    DATABASE_URL=os.getenv("DATABASE_URL")
)

redis_config = RedisConifg(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"))

rmq_cli_config = RMQConifg(
    rmq_url = os.getenv("RMQ_URL")
)


print(rmq_cli_config)
