from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from api.database.models.models import MLScore
from api.deps import get_session
from api.schemas.advertiser import MLScoreSchema

router = APIRouter(tags=["Advertisers"])

@router.post("/ml-scores", status_code=status.HTTP_201_CREATED)
async def upsert_ml_score(
    ml_score: MLScoreSchema,
    session: AsyncSession = Depends(get_session)
):

    try:
        result_score = await session.execute(
            select(MLScore).where(
                MLScore.client_id == ml_score.client_id,
                MLScore.advertiser_id == ml_score.advertiser_id
            )
        )
        existing_ml_score = result_score.scalar_one_or_none()
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Нет клиента/рекламодателя с такими ID"
        )

    try:
        if existing_ml_score:
            existing_ml_score.score = ml_score.score
        else:
            new_ml_score = MLScore(
                client_id=ml_score.client_id,
                advertiser_id=ml_score.advertiser_id,
                score=ml_score.score
            )
            session.add(new_ml_score)
        await session.commit()
    except Exception as e:
        print(e)
        await session.rollback()
        raise HTTPException(
            status_code=404,
            detail=f"Нет клиента/рекламодателя с такими ID"
        )

    return {
        "client_id": ml_score.client_id,
        "advertiser_id": ml_score.advertiser_id,
        "score": ml_score.score
    }