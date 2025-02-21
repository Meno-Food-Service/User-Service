from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SCreateUserRequest(BaseModel):
    username: str
    password: str
    name: str
    email: str
    phone_number: str
    role: Optional[str] = None
    location: str


class SUser(BaseModel):
    id: int
    username: str
    name: Optional[str] = None
    phone_number: str
    password: Optional[str] = None


class SUpdatePassword(BaseModel):
    old_password: str
    new_password: str


class SUpdateUser(BaseModel):
    name: str
    phone_number: str
    location: str
