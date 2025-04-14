from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.database.models.models import Advertiser as AdvertiserModel
from api.deps import get_session
from api.schemas.advertiser import AdvertiserResponse, AdvertiserUpsert
from api.schemas.campaign import *

router = APIRouter(prefix="/advertisers", tags=["Advertisers"])


@router.get("/{advertiserId}", response_model=AdvertiserResponse)
async def get_advertiser_by_id(advertiserId: UUID, session: AsyncSession = Depends(get_session)):
    advertiser = await session.get(AdvertiserModel, advertiserId)
    if not advertiser:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertiser not found")
    return advertiser


@router.post("/bulk", response_model=List[AdvertiserResponse], status_code=status.HTTP_201_CREATED)
async def upsert_advertisers(advertisers: List[AdvertiserUpsert], session: AsyncSession = Depends(get_session)):
    result_advertisers = []
    for adv_data in advertisers:
        advertiser = await session.get(AdvertiserModel, adv_data.advertiser_id)
        if advertiser:
            advertiser.name = adv_data.name
        else:
            advertiser = AdvertiserModel(
                advertiser_id=adv_data.advertiser_id,
                name=adv_data.name
            )
            session.add(advertiser)
        result_advertisers.append(advertiser)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Duplicate advertiser record") from e
    return result_advertisers
