from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.user.models import UserModel
from redis.asyncio import StrictRedis
from aio_pika import RobustConnection
from sqlalchemy import select
from services.user.scheme import SCreateUserRequest, SUser, SUpdatePassword, SUpdateUser
from services.user.utils import Hash, publish_message
from typing import TypeVar, Type, Optional, Dict, Union, Any, Tuple, Iterable
from fastapi.encoders import jsonable_encoder
import logging
import json
import httpx


T = TypeVar("T")
log = logging.getLogger(__name__)


class UserService:
    def __init__(
        self,
        session: AsyncSession = None,
        redis_cli: StrictRedis = None,
        rmq_cli: RobustConnection = None,
        current_user: SUser = None,
    ):
        self.session = session
        self.redis_cli = redis_cli
        self.rmq_cli = rmq_cli
        self.current_user = current_user

    async def _create_user(self, request: SCreateUserRequest):
        exist_user = (
            (
                await self.session.execute(
                    select(UserModel).filter_by(email=request.email)
                )
            )
            .scalars()
            .first()
        )

        if exist_user:
            log.info("User all ready exist %s", request.username)
            raise HTTPException(detail="User all ready exist", status_code=403)

        hashed_password = Hash.bcrypt(request.password)

        request.password = hashed_password
        user = UserModel(**request.__dict__)
        self.session.add(user)
        await self.session.commit()

        if request.role == "Курьер":
            log.info("Создёться профиль для %s", request.role)
            await self._request_to_url(
                f"http://localhost:8082/courer/service/api/v1/create-courer/",
                method="post",
            )

        return SCreateUserRequest(**request.__dict__)

    async def _get_user(self, pk: int) -> Optional[SUser]:
        cached_data = await self._get_data_from_cache(f"get-user-{pk}")
        if cached_data:
            await publish_message(
                message=json.dumps(cached_data),
                queues_name=f"get-user-{pk}",
                connetcion=self.rmq_cli,
            )

            return cached_data

        response = await self._get_object(
            model=UserModel, response=SUser, field=pk, field_name="id"
        )

        response.password = None
        await self.redis_cli.setex(f"get-user-{pk}", 300, json.dumps(response.dict()))
        await publish_message(
            message=json.dumps(response.dict()),
            queues_name=f"get-user-{response.id}",
            connetcion=self.rmq_cli,
        )
        return response


    async def _get_user_by_username_password(
        self, username: str, password: str
    ) -> Optional[SUser]:
        response = await self._get_object(
            model=UserModel, response=SUser, field=username, field_name="username"
        )

        if not Hash.verify_password(password, response.password):
            log.info("User password error")
            raise HTTPException(
                detail="Password incorrect please write correct password",
                status_code=403,
            )

        response.password = None
        await publish_message(
            message=json.dumps(response.dict()),
            connetcion=self.rmq_cli,
            queues_name=f"get-user-by-username-{response.username}",
        )

        return response

    async def _get_user_by_username(self, username: str) -> Optional[SUser]:

        cached_data = await self._get_data_from_cache(
            f"get-user-by-username-{username}"
        )
        if cached_data:

            await publish_message(
                message=json.dumps(cached_data),
                queues_name=f"get-user-by-username-{username}",
                connetcion=self.rmq_cli,
            )

            return cached_data

        response = await self._get_object(
            model=UserModel, field=username, field_name="username", response=SUser
        )

        response.password = None
        await publish_message(
            message=json.dumps(response.dict()),
            queues_name=f"get-user-by-username-{username}",
            connetcion=self.rmq_cli,
        )

        await self.redis_cli.setex(
            f"get-user-by-username-{username}", 300, json.dumps(response.dict())
        )

        return response

    async def _get_user_me(self) -> SUser:
        cached_data = await self._get_data_from_cache(
            f"get-user-{self.current_user.id}"
        )
        if cached_data:
            return cached_data

        return await self._get_object(
            model=UserModel,
            response=SUser,
            field_name="id",
            field=self.current_user.id,
        )

    async def _update_password(self, request: SUpdatePassword):
        user = (
            (
                await self.session.execute(
                    select(UserModel).filter_by(id=self.current_user.id)
                )
            )
            .scalars()
            .first()
        )

        if not user:
            log.info("User not found")
            raise HTTPException(
                detail="User not found {self.current_user.id}", status_code=404
            )

        if not Hash.verify_password(request.old_password, user.password):
            log.info("Passwords didint matching")
            raise HTTPException(detail="Passwords didint matching", status_code=403)

        hashed_password = Hash.bcrypt(request.new_password)
        user.password = hashed_password

        log.info("Password updated succsesfully")
        await self.session.commit()
        return {"detail": "Password Updated Succsesfully"}

    async def _update_profile(self, request: SUpdateUser) -> SUpdateUser:
        return await self._update_obj(
            model=UserModel,
            request=request,
            field_name="id",
            field=self.current_user.id,
            status_code=404,
            detail="User Obj not found",
        )

    async def _update_obj(
        self,
        model: Type[T],
        request: Type[T],
        field: Any,
        field_name: str,
        detail: str,
        status_code: int,
    ) -> T:

        obj = (
            (
                await self.session.execute(
                    select(model).filter(getattr(model, field_name) == field)
                )
            )
            .scalars()
            .first()
        )

        if not obj:
            raise HTTPException(detail=detail, status_code=status_code)

        if isinstance(request, dict):
            for field, value in request.items():
                setattr(obj, field, value)
        elif isinstance(request, list):
            for field, value in request:
                setattr(obj, field, value)

        await self.session.commit()
        return obj

    async def _get_object(
        self, model: Type[T], response: Type[T], field: Type[T], field_name: str
    ) -> Type[T]:
        obj = (
            (
                await self.session.execute(
                    select(model).filter(getattr(model, field_name) == field)
                )
            )
            .scalars()
            .first()
        )

        if not obj:
            log.info("Obj not found")
            raise HTTPException(detail="Not found", status_code=404)

        return response(**obj.__dict__)

    async def _get_data_from_cache(self, key) -> json:
        cached_data = await self.redis_cli.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None

    async def _request_to_url(self, url, method):
        async with httpx.AsyncClient() as cl:
            response = await cl.request(method=method, url=url)
            return response
