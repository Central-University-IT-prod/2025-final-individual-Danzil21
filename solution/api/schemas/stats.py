from pydantic import BaseModel, Field


class StatsResponse(BaseModel):
    impressions_count: int = Field(..., description="Уникальные показы")
    clicks_count: int = Field(..., description="Уникальные клики")
    conversion: float = Field(..., description="Коэффициент конверсии (в процентах)")
    spent_impressions: float = Field(..., description="Затраты на показы")
    spent_clicks: float = Field(..., description="Затраты на клики")
    spent_total: float = Field(..., description="Суммарные затраты")

    class Config:
        from_attributes = True


class DailyStatsResponse(StatsResponse):
    date: int = Field(..., description="День, за который собрана статистика")

    class Config:
        from_attributes = True
