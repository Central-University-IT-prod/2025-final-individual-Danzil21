from typing import Optional
from urllib.parse import urlparse
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator


class Targeting(BaseModel):
    gender: Optional[str] = Field(
        None,
        description="Пол аудитории для показа объявления (MALE, FEMALE или ALL)"
    )
    age_from: Optional[int] = Field(
        None,
        ge=0,
        description="Минимальный возраст аудитории (включительно)"
    )
    age_to: Optional[int] = Field(
        None,
        ge=0,
        description="Максимальный возраст аудитории (включительно)"
    )
    location: Optional[str] = Field(
        None,
        description="Локация аудитории"
    )

    @field_validator('gender')
    def validate_gender(cls, v):
        if v is None:
            return v
        allowed = {"MALE", "FEMALE", "ALL"}
        if v is not None and v not in allowed:
            raise HTTPException(
                status_code=422,
                detail=f"Gender must be one of {allowed}")
        return v

    @field_validator('age_to')
    def validate_age_range(cls, v, info):
        if v is None:
            return v
        age_from = info.data.get("age_from")
        if v is not None and age_from is not None and v < age_from:
            raise HTTPException(
                status_code=422,
                detail="age_to must be greater than or equal to age_from")
        return v

    class Config:
        from_attributes = True
        populate_by_name = True


class CampaignBase(BaseModel):
    impressions_limit: int = Field(
        ...,
        gt=0,
        description="Лимит показов"
    )
    clicks_limit: int = Field(
        ...,
        gt=0,
        description="Лимит переходов"
    )
    cost_per_impression: float = Field(
        ...,
        gt=0,
        description="Стоимость одного показа"
    )
    cost_per_click: float = Field(
        ...,
        gt=0,
        description="Стоимость одного клика"
    )
    ad_title: str = Field(
        ...,
        min_length=1,
        description="Название объявления"
    )
    ad_text: str = Field(
        ...,
        min_length=1,
        description="Текст рекламного объявления"
    )
    ad_photo_url: Optional[str] = Field(
        None,
        description="Ссылка на фото объявления. Должна начинаться с http:// или https://"
    )
    start_date: int = Field(
        ...,
        ge=0,
        description="День начала кампании"
    )
    end_date: int = Field(
        ...,
        ge=0,
        description="День окончания кампании"
    )
    targeting: Targeting

    @field_validator('ad_title', 'ad_text')
    def non_empty_trimmed(cls, v: str) -> str:

        v = v.strip()
        if not v:
            raise HTTPException(
                status_code=422,
                detail="Поле не может быть пустым или состоять только из пробелов")
        return v

    @field_validator('ad_photo_url')
    def validate_ad_photo_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise HTTPException(
                status_code=422,
                detail="Ссылка на фото не может быть пустой")
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise HTTPException(
                status_code=422,
                detail="Ссылка должна начинаться с http:// или https://")
        if not parsed.netloc:
            raise HTTPException(
                status_code=422,
                detail="Ссылка должна содержать корректный домен")
        return v

    @field_validator('end_date')
    def end_date_after_start(cls, v, info):
        start = info.data.get("start_date")
        if start is not None and v < start:
            raise HTTPException(
                status_code=422,
                detail="end_date must be greater than or equal to start_date")
        return v

    class Config:
        from_attributes = True
        populate_by_name = True
        use_enum_values = True


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    impressions_limit: Optional[int] = Field(
        None,
        gt=0,
        description="Лимит показов"
    )
    clicks_limit: Optional[int] = Field(
        None,
        gt=0,
        description="Лимит переходов"
    )
    cost_per_impression: Optional[float] = Field(
        None,
        gt=0,
        description="Стоимость одного показа"
    )
    cost_per_click: Optional[float] = Field(
        None,
        gt=0,
        description="Стоимость одного клика"
    )
    ad_title: Optional[str] = Field(
        None,
        min_length=1,
        description="Название объявления"
    )
    ad_text: Optional[str] = Field(
        None,
        min_length=1,
        description="Текст рекламного объявления"
    )
    ad_photo_url: Optional[str] = Field(
        None,
        description="Ссылка на фото объявления. Должна начинаться с http:// или https://"
    )
    start_date: Optional[int] = Field(
        None,
        ge=0,
        description="День начала кампании"
    )
    end_date: Optional[int] = Field(
        None,
        ge=0,
        description="День окончания кампании"
    )
    targeting: Optional[Targeting] = None

    @field_validator('ad_photo_url')
    def validate_ad_photo_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise HTTPException(
                status_code=422,
                detail="Ссылка на фото не может быть пустой")
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise HTTPException(
                status_code=422,
                detail="Ссылка должна начинаться с http:// или https://")
        if not parsed.netloc:
            raise HTTPException(
                status_code=422,
                detail="Ссылка должна содержать корректный домен")
        return v

    @field_validator('ad_title', 'ad_text', mode="before")
    def non_empty_if_provided(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise HTTPException(
                status_code=422,
                detail="Field cannot be empty or whitespace")
        return v

    class Config:
        from_attributes = True
        populate_by_name = True


class CampaignResponse(CampaignBase):
    campaign_id: UUID = Field(alias="campaign_id")
    advertiser_id: UUID

    class Config:
        from_attributes = True
        populate_by_name = True
        use_enum_values = True
