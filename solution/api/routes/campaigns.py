import traceback
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from api.deps import get_session
from api.database.models.models import Campaign, Advertiser
from api.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse
from api.utils.get_neuro_json import extract_json_to_dict
from api.utils.neuro import moderate_ads, generate_ad_text
from app.core.config import settings

router = APIRouter(prefix="/advertisers/{advertiserId}/campaigns", tags=["Campaigns"])


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
        advertiserId: UUID,
        campaign_data: CampaignCreate,
        generate_text: Optional[bool] = False,
        session: AsyncSession = Depends(get_session)
):
    advertiser = await session.get(Advertiser, advertiserId)
    if not advertiser:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertiser not found")


    if generate_text:
        try:
            ad_text = await generate_ad_text(campaign_data.ad_title)
            neuro_json = extract_json_to_dict(ad_text)
            campaign_data.ad_text = neuro_json.get('ad_text')
        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(status_code=400, detail="Ad text is not allowed")

    if (campaign_data.ad_text or campaign_data.ad_title) and settings.MODERATE_ADS:
        try:
            metadata = await moderate_ads(campaign_data.ad_title, campaign_data.ad_text)
            print(metadata)
            neuro_json = extract_json_to_dict(metadata)
            print(neuro_json)
        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(status_code=400, detail="Ad text is not allowed")
        else:
            if neuro_json.get('passed') is False:
                raise HTTPException(status_code=400, detail="Ad text is not allowed")

    new_campaign = Campaign(
        advertiser_id=advertiserId,
        impressions_limit=campaign_data.impressions_limit,
        clicks_limit=campaign_data.clicks_limit,
        cost_per_impression=campaign_data.cost_per_impression,
        cost_per_click=campaign_data.cost_per_click,
        ad_title=campaign_data.ad_title,
        ad_text=campaign_data.ad_text,
        start_date=campaign_data.start_date,
        end_date=campaign_data.end_date,
        target_gender=campaign_data.targeting.gender,
        target_age_from=campaign_data.targeting.age_from,
        target_age_to=campaign_data.targeting.age_to,
        target_location=campaign_data.targeting.location,
        is_deleted=False
    )
    session.add(new_campaign)
    try:
        await session.commit()
        await session.refresh(new_campaign)
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Campaign creation failed") from e

    return new_campaign


@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
        advertiserId: UUID,
        page: int = Query(1, ge=1, description="Номер страницы"),
        size: int = Query(10, ge=1, description="Количество элементов на странице"),
        session: AsyncSession = Depends(get_session)
):
    advertiser = await session.get(Advertiser, advertiserId)
    if not advertiser:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertiser not found")

    offset = (page - 1) * size
    query = (
        select(Campaign)
        .where(Campaign.advertiser_id == advertiserId, Campaign.is_deleted == False)
        .order_by(Campaign.create_date.desc())
        .offset(offset)
        .limit(size)
    )
    result = await session.execute(query)
    campaigns = result.scalars().all()
    return campaigns


@router.get("/{campaignId}", response_model=CampaignResponse)
async def get_campaign(
        advertiserId: UUID,
        campaignId: UUID,
        session: AsyncSession = Depends(get_session)
):
    campaign = await session.get(Campaign, campaignId)
    if not campaign or campaign.advertiser_id != advertiserId or campaign.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


@router.put("/{campaignId}", response_model=CampaignResponse)
async def update_campaign(
        advertiserId: UUID,
        campaignId: UUID,
        campaign_data: CampaignUpdate,
        session: AsyncSession = Depends(get_session)
):
    campaign = await session.get(Campaign, campaignId)
    if not campaign or campaign.advertiser_id != advertiserId or campaign.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    update_data = campaign_data.model_dump(exclude_unset=True)

    if "targeting" in update_data:
        targeting_data = update_data.pop("targeting")
        if targeting_data is not None:
            if targeting_data.get("gender") is not None:
                campaign.target_gender = targeting_data.get("gender")
            if targeting_data.get("age_from") is not None:
                campaign.target_age_from = targeting_data.get("age_from")
            if targeting_data.get("age_to") is not None:
                campaign.target_age_to = targeting_data.get("age_to")
            if targeting_data.get("location") is not None:
                campaign.target_location = targeting_data.get("location")

    print(update_data.items())
    for field, value in update_data.items():
        if value is not None:
            setattr(campaign, field, value)

    new_start_date = campaign.start_date
    new_end_date = campaign.end_date

    if new_start_date is not None and new_end_date is not None and new_start_date > new_end_date:
         raise HTTPException(status_code=400, detail="end_date must be greater than or equal to start_date")

    if campaign.target_age_from is not None and campaign.target_age_to is not None:
        if campaign.target_age_from > campaign.target_age_to:
            raise HTTPException(status_code=400, detail="target_age_to must be greater than or equal to target_age_from")

    try:
        await session.commit()
        await session.refresh(campaign)
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Campaign update failed") from e

    return campaign


@router.delete("/{campaignId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
        advertiserId: UUID,
        campaignId: UUID,
        session: AsyncSession = Depends(get_session)
):
    campaign = await session.get(Campaign, campaignId)
    if not campaign or campaign.advertiser_id != advertiserId or campaign.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    campaign.is_deleted = True
    await session.commit()
    return None

