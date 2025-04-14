from pydantic import BaseModel, Field


class TimeAdvanceRequest(BaseModel):
    current_date: int = Field(
        ...,
        ge=0,
        description="Текущий день"
    )


class TimeAdvanceResponse(BaseModel):
    current_date: int = Field(
        ...,
        description="Установленный текущий день"
    )
