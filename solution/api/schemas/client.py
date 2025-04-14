from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field
from pydantic.v1 import validator

from api.database.models.models import ClientGenderEnum


class ClientResponse(BaseModel):
    id: UUID = Field(alias="client_id")

    login: str
    age: int
    location: str
    gender: str

    class Config:
        from_attributes = True
        populate_by_name = True
        use_enum_values = True


class ClientUpsert(BaseModel):
    id: UUID = Field(..., alias="client_id")
    login: str = Field(..., min_length=1, description="Логин не может быть пустым")
    age: int = Field(..., gt=0, description="Возраст должен быть положительным числом")
    location: str = Field(..., min_length=1, description="Локация не может быть пустой")
    gender: ClientGenderEnum = Field(..., description="Пол должен быть 'MALE' или 'FEMALE'")

    @validator('login')
    def validate_login(cls, v: str) -> str:
        if not v.strip():
            raise HTTPException(
                status_code=422,
                detail="Логин не может состоять только из пробелов")
        return v

    @validator('location')
    def validate_location(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise HTTPException(
                status_code=422,
                detail="Локация не может быть пустой")
        allowed_chars = set(" -")
        for char in v:
            if not (char.isalpha() or char in allowed_chars):
                raise HTTPException(
                status_code=422,
                detail="Локация должна содержать только буквы, пробелы и дефисы")
        return v

    @validator('gender', pre=True)
    def validate_gender(cls, v):
        if isinstance(v, str):
            return v.upper().strip()
        return v

    class Config:
        populate_by_name = True
        use_enum_values = True
