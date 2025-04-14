from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.deps import get_session
from api.database.models.models import SystemTime
from api.schemas.time import TimeAdvanceRequest, TimeAdvanceResponse

router = APIRouter(prefix="/time", tags=["Time"])


@router.post("/advance", response_model=TimeAdvanceResponse)
async def advance_day(
        body: TimeAdvanceRequest,
        session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(SystemTime).limit(1))
    row = result.scalar_one_or_none()

    if row is None:
        row = SystemTime(current_date=body.current_date)
        session.add(row)
    else:
        row.current_date = body.current_date

    await session.commit()
    await session.refresh(row)

    return TimeAdvanceResponse(current_date=row.current_date)


@router.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}