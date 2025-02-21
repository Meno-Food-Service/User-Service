from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependcies.dependcies import (
    get_user_session,
    get_redis,
    get_rmq,
    get_current_user,
)
from redis.asyncio import StrictRedis
from aio_pika import RobustConnection
from services.user.service import UserService
from services.user.scheme import SUser, SCreateUserRequest, SUpdatePassword, SUpdateUser


user_router = APIRouter(tags=["User Service API"], prefix="/user-service/api/v1")


@user_router.post("/create-user/", response_model=SCreateUserRequest)
async def create_user(
    request: SCreateUserRequest, session: AsyncSession = Depends(get_user_session)
):
    service = UserService(session=session)
    return await service._create_user(request=request)


@user_router.get("/get-user/{pk}/", response_model=SUser)
async def get_user(
    pk: int,
    session: AsyncSession = Depends(get_user_session),
    redis_cli: StrictRedis = Depends(get_redis),
    rmq_cli: RobustConnection = Depends(get_rmq),
):
    service = UserService(session=session, redis_cli=redis_cli, rmq_cli=rmq_cli)
    return await service._get_user(pk=pk)


@user_router.get(
    "/get-user-by-username-password/{username}/{password}", response_model=SUser
)
async def get_user_by_username_password(
    username: str,
    password: str,
    session: AsyncSession = Depends(get_user_session),
    rmq_cli: RobustConnection = Depends(get_rmq),
):
    service = UserService(session=session, rmq_cli=rmq_cli)
    return await service._get_user_by_username_password(
        username=username, password=password
    )


@user_router.get("/get-user-by-username/{username}", response_model=SUser)
async def get_user_by_username(
    username: str,
    session: AsyncSession = Depends(get_user_session),
    redis_cli: StrictRedis = Depends(get_redis),
    rmq_cli: RobustConnection = Depends(get_rmq),
):
    service = UserService(session=session, rmq_cli=rmq_cli, redis_cli=redis_cli)
    return await service._get_user_by_username(username=username)


@user_router.patch("/update-password/")
async def update_password(
    request: SUpdatePassword,
    session: AsyncSession = Depends(get_user_session),
    current_user: SUser = Depends(get_current_user),
):
    service = UserService(session=session, current_user=current_user)
    return await service._update_password(request=request)


@user_router.patch("/update-profile/", response_model=SUpdateUser)
async def update_profile(
    request: SUpdateUser,
    session: AsyncSession = Depends(get_user_session),
    current_user: SUser = Depends(get_current_user),
):
    service = UserService(session=session, current_user=current_user)
    return await service._update_profile(request=request)
