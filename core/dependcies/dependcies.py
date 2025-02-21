from redis.asyncio import StrictRedis
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from core.database.user import async_session
from aio_pika import connect_robust, RobustConnection
from typing import TypeVar, Type
from config.config import redis_config, rmq_cli_config
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncContextManager, AsyncGenerator
from jose import jwt, JWTError
from services.user.scheme import SUser
from sqlalchemy import select
from services.user.models import UserModel
from dotenv import load_dotenv
import os
import json
import logging

rmq_url = rmq_cli_config.rmq_url

load_dotenv()

log = logging.getLogger(__name__)


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

oauth2_bearer = OAuth2PasswordBearer(
    "http://localhost:8081/auth-service/api/v1/auth/login/"
)


async def get_redis() -> StrictRedis:
    return await StrictRedis(host=redis_config.host, port=redis_config.port)


async def get_rmq():

    connection = await connect_robust(
        url=rmq_url
    )

    print(connection)

    try:
        yield connection
    finally:
        await connection.close()


async def get_user_session() -> AsyncGenerator[AsyncContextManager, AsyncSession]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    token: str = Depends(oauth2_bearer),
    session: AsyncSession = Depends(get_user_session),
) -> SUser:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = (
        (await session.execute(select(UserModel).filter_by(username=user_id)))
        .scalars()
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return SUser(**user.__dict__)
