from uuid import UUID
from typing import List
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, distinct, literal, Numeric
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.deps import get_session
from api.database.models.models import Campaign, AdEvent, AdEventTypeEnum, Advertiser
from api.schemas.stats import StatsResponse, DailyStatsResponse

router = APIRouter(prefix="/stats", tags=["Statistics"])


async def _compute_campaigns_aggregated_stats(
    session: AsyncSession,
    campaign_ids: List[UUID]
) -> StatsResponse:
    if not campaign_ids:
        return StatsResponse(
            impressions_count=0,
            clicks_count=0,
            conversion=0.0,
            spent_impressions=0.0,
            spent_clicks=0.0,
            spent_total=0.0
        )

    campaigns_query = select(Campaign).where(Campaign.campaign_id.in_(campaign_ids))
    campaigns = (await session.execute(campaigns_query)).scalars().all()
    if not campaigns:
        return StatsResponse(
            impressions_count=0,
            clicks_count=0,
            conversion=0.0,
            spent_impressions=0.0,
            spent_clicks=0.0,
            spent_total=0.0
        )

    cost_map = {
        c.campaign_id: (c.cost_per_impression, c.cost_per_click)
        for c in campaigns
    }

    stmt = (
        select(
            AdEvent.campaign_id,
            AdEvent.event_type,
            func.count(distinct(AdEvent.client_id)).label("unique_cnt")
        )
        .where(AdEvent.campaign_id.in_(campaign_ids))
        .group_by(AdEvent.campaign_id, AdEvent.event_type)
    )
    rows = (await session.execute(stmt)).all()

    total_impr = 0
    total_clicks = 0
    total_spent_impr = 0.0
    total_spent_clicks = 0.0

    for row in rows:
        cid = row[0]
        etype = row[1]
        unique_cnt = row[2]

        cost_per_impression, cost_per_click = cost_map[cid]

        if etype == AdEventTypeEnum.IMPRESSION:
            total_impr += unique_cnt
            total_spent_impr += cost_per_impression * unique_cnt
        else:
            total_clicks += unique_cnt
            total_spent_clicks += cost_per_click * unique_cnt

    spent_total = total_spent_impr + total_spent_clicks
    conversion = (total_clicks / total_impr * 100.0) if total_impr > 0 else 0.0

    return StatsResponse(
        impressions_count=total_impr,
        clicks_count=total_clicks,
        conversion=conversion,
        spent_impressions=total_spent_impr,
        spent_clicks=total_spent_clicks,
        spent_total=spent_total
    )


async def _compute_campaigns_daily_stats(
    session: AsyncSession,
    campaign_ids: List[UUID]
) -> List[DailyStatsResponse]:
    if not campaign_ids:
        return []

    campaigns_query = select(Campaign).where(Campaign.campaign_id.in_(campaign_ids))
    campaigns = (await session.execute(campaigns_query)).scalars().all()
    if not campaigns:
        return []

    cost_map = {
        c.campaign_id: (c.cost_per_impression, c.cost_per_click)
        for c in campaigns
    }

    day_expr = AdEvent.event_day.label("day_int")

    stmt = (
        select(
            AdEvent.campaign_id,
            day_expr,
            AdEvent.event_type,
            func.count(distinct(AdEvent.client_id)).label("unique_cnt")
        )
        .where(AdEvent.campaign_id.in_(campaign_ids))
        .group_by(AdEvent.campaign_id, AdEvent.event_day, AdEvent.event_type)
        .order_by(AdEvent.campaign_id, AdEvent.event_day)
    )
    rows = (await session.execute(stmt)).all()

    aggregator = defaultdict(lambda: {"impr": 0, "click": 0})

    for row in rows:
        cid = row[0]
        day_val = int(row[1])
        ev_type = row[2]
        unique_cnt = row[3]

        if ev_type == AdEventTypeEnum.IMPRESSION:
            aggregator[(cid, day_val)]["impr"] += unique_cnt
        else:
            aggregator[(cid, day_val)]["click"] += unique_cnt

    result = []
    for (cid, day_val), counters in aggregator.items():
        cost_i, cost_c = cost_map[cid]
        impr_count = counters["impr"]
        click_count = counters["click"]

        spent_impr = cost_i * impr_count
        spent_clicks = cost_c * click_count
        spent_total = spent_impr + spent_clicks
        conv = (click_count / impr_count * 100) if impr_count > 0 else 0.0

        result.append(DailyStatsResponse(
            date=day_val,
            impressions_count=impr_count,
            clicks_count=click_count,
            conversion=conv,
            spent_impressions=spent_impr,
            spent_clicks=spent_clicks,
            spent_total=spent_total
        ))

    result.sort(key=lambda x: x.date)
    return result



@router.get("/campaigns/{campaignId}", response_model=StatsResponse)
async def get_campaign_stats(campaignId: UUID, session: AsyncSession = Depends(get_session)):
    campaign = await session.get(Campaign, campaignId)
    if not campaign or campaign.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    stats = await _compute_campaigns_aggregated_stats(session, [campaignId])
    return stats


@router.get("/advertisers/{advertiserId}/campaigns", response_model=StatsResponse)
async def get_advertiser_campaigns_stats(advertiserId: UUID, session: AsyncSession = Depends(get_session)):
    advertiser = await session.get(
        Advertiser,
        advertiserId,
        options=[joinedload(Advertiser.campaigns)]
    )
    if not advertiser:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertiser not found")

    campaigns = advertiser.campaigns
    if not campaigns:
        return StatsResponse(
            impressions_count=0,
            clicks_count=0,
            conversion=0.0,
            spent_impressions=0.0,
            spent_clicks=0.0,
            spent_total=0.0
        )

    campaign_ids = [c.campaign_id for c in campaigns]
    stats = await _compute_campaigns_aggregated_stats(session, campaign_ids)
    return stats


@router.get("/campaigns/{campaignId}/daily", response_model=List[DailyStatsResponse])
async def get_campaign_daily_stats(campaignId: UUID, session: AsyncSession = Depends(get_session)):
    campaign = await session.get(Campaign, campaignId)
    if not campaign or campaign.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    result = await _compute_campaigns_daily_stats(session, [campaignId])
    return result


@router.get("/advertisers/{advertiserId}/campaigns/daily", response_model=List[DailyStatsResponse])
async def get_advertiser_daily_stats(advertiserId: UUID, session: AsyncSession = Depends(get_session)):
    advertiser = await session.get(
        Advertiser,
        advertiserId,
        options=[joinedload(Advertiser.campaigns)]
    )
    if not advertiser:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertiser not found")

    campaigns = advertiser.campaigns
    if not campaigns:
        return []

    campaign_ids = [c.campaign_id for c in campaigns]
    data = await _compute_campaigns_daily_stats(session, campaign_ids)
    if not data:
        return []

    aggregator = defaultdict(lambda: {
        "impr": 0,
        "click": 0,
        "spent_impr": 0.0,
        "spent_clicks": 0.0
    })

    for dstat in data:
        day_val = dstat.date
        aggregator[day_val]["impr"] += dstat.impressions_count
        aggregator[day_val]["click"] += dstat.clicks_count
        aggregator[day_val]["spent_impr"] += dstat.spent_impressions
        aggregator[day_val]["spent_clicks"] += dstat.spent_clicks

    result = []
    for day_val, agg in aggregator.items():
        impr_count = agg["impr"]
        click_count = agg["click"]
        spent_i = agg["spent_impr"]
        spent_c = agg["spent_clicks"]
        spent_total = spent_i + spent_c
        conv = (click_count / impr_count * 100.0) if impr_count > 0 else 0.0
        result.append(DailyStatsResponse(
            date=day_val,
            impressions_count=impr_count,
            clicks_count=click_count,
            conversion=conv,
            spent_impressions=spent_i,
            spent_clicks=spent_c,
            spent_total=spent_total
        ))

    result.sort(key=lambda x: x.date)
    return result
