from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from uuid import UUID

from sqlalchemy import func, asc
from sqlalchemy import (
    select,
    distinct,
    literal,
    or_,
    desc,
    case as sql_case
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import case as sql_case2

from api.deps import get_session
from api.database.models.models import (
    Campaign,
    AdEvent,
    AdEventTypeEnum,
    Client,
    MLScore,
    SystemTime,
    TargetingGenderEnum,
)
from api.schemas.ads import AdResponse, AdClickRequest

router = APIRouter(prefix="/ads", tags=["Ads"])


async def get_current_day(session: AsyncSession) -> int:
    """Получаем текущий день из таблицы system_time; если нет — 0."""
    result = await session.execute(
        select(SystemTime.current_date)
        .order_by(desc(SystemTime.id))
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return row if row is not None else 0


@router.get("", response_model=AdResponse)
async def get_ad_for_client(
    client_id: UUID = Query(...),
    session: AsyncSession = Depends(get_session),
):
    client_obj = await session.get(Client, client_id)
    if not client_obj:
        raise HTTPException(status_code=404, detail="Client not found")

    current_day = await get_current_day(session)

    impression_case = sql_case(
        (AdEvent.event_type == AdEventTypeEnum.IMPRESSION, AdEvent.client_id),
        else_=None
    )
    click_case = sql_case(
        (AdEvent.event_type == AdEventTypeEnum.CLICK, AdEvent.client_id),
        else_=None
    )
    campaign_stats = (
        select(
            AdEvent.campaign_id.label("cid"),
            func.count(distinct(impression_case)).label("unique_impressions"),
            func.count(distinct(click_case)).label("unique_clicks"),
        )
        .group_by(AdEvent.campaign_id)
        .subquery()
    )

    client_events = (
        select(
            AdEvent.campaign_id.label("cid"),
            func.bool_or(AdEvent.event_type == AdEventTypeEnum.IMPRESSION).label("user_has_impression"),
            func.bool_or(AdEvent.event_type == AdEventTypeEnum.CLICK).label("user_has_click"),
        )
        .where(AdEvent.client_id == client_id)
        .group_by(AdEvent.campaign_id)
        .subquery()
    )

    ml_scores_subq = (
        select(
            MLScore.advertiser_id.label("adv_id"),
            MLScore.client_id.label("c_id"),
            MLScore.score.label("ml_score"),
        )
        .where(MLScore.client_id == client_id)
        .subquery()
    )

    c = Campaign
    cs = campaign_stats
    ce = client_events
    ms = ml_scores_subq

    ui_col = func.coalesce(cs.c.unique_impressions, 0)
    uc_col = func.coalesce(cs.c.unique_clicks, 0)

    is_not_dead = or_(ui_col < c.impressions_limit, uc_col < c.clicks_limit)

    has_impr_col = func.coalesce(ce.c.user_has_impression, literal(False))
    has_click_col = func.coalesce(ce.c.user_has_click, literal(False))

    filter_impr_ok = or_(has_impr_col == True, ui_col < c.impressions_limit)
    filter_click_ok = or_(has_click_col == True, uc_col < c.clicks_limit)

    k = 0.001
    m0 = 5000.0
    ml_s = func.coalesce(ms.c.ml_score, 0.0)
    p_click_expr = 1.0 / (1.0 + func.exp(-k * (ml_s - m0)))
    expected_profit_expr = sql_case2(
        (has_impr_col == True,
            sql_case2(
                (has_click_col == True, 0.0),
                else_=c.cost_per_click * p_click_expr
            )
        ),
        else_=(c.cost_per_impression + c.cost_per_click * p_click_expr)
    )

    client_age = client_obj.age or 0
    client_loc = client_obj.location or ""
    client_gender_val = client_obj.gender.value if client_obj.gender else None

    filter_gender = or_(
        c.target_gender == None,
        c.target_gender == TargetingGenderEnum.ALL,
        c.target_gender == client_gender_val
    )
    filter_age_from = or_(c.target_age_from == None, c.target_age_from <= client_age)
    filter_age_to   = or_(c.target_age_to   == None, c.target_age_to   >= client_age)
    filter_location = or_(c.target_location == None, c.target_location == "", c.target_location == client_loc)

    stmt = (
        select(
            c.campaign_id,
            c.advertiser_id,
            c.ad_title,
            c.ad_text,
            c.ad_photo_url,
            has_impr_col.label("user_has_impression"),
            has_click_col.label("user_has_click"),
            ui_col.label("unique_impressions"),
            uc_col.label("unique_clicks"),
            c.impressions_limit,
            c.clicks_limit,
            c.cost_per_impression,
            c.cost_per_click,
        )
        .add_columns(
            expected_profit_expr.label("expected_profit"),
            ml_s.label("calc_ml_score"),
        )
        .join(ce, ce.c.cid == c.campaign_id, isouter=True)
        .join(cs, cs.c.cid == c.campaign_id, isouter=True)
        .join(ms, ms.c.adv_id == c.advertiser_id, isouter=True)
        .where(c.is_deleted == False)
        .where(c.start_date <= current_day)
        .where(c.end_date >= current_day)
        .where(is_not_dead)
        .where(filter_impr_ok)
        .where(filter_click_ok)
        .where(filter_gender)
        .where(filter_age_from)
        .where(filter_age_to)
        .where(filter_location)
        .order_by(desc("expected_profit"), desc("calc_ml_score"))
        .limit(1)
    )

    row = (await session.execute(stmt)).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="No suitable campaign found")

    best_campaign_id = row["campaign_id"]
    user_has_impr = row["user_has_impression"]

    if not user_has_impr:
        success = await safe_record_impression(
            campaign_id=best_campaign_id,
            client_id=client_id,
            session=session
        )
        if not success:
            raise HTTPException(
                status_code=404,
                detail="No suitable campaign found (limit)"
            )

    return AdResponse(
        ad_id=row["campaign_id"],
        ad_title=row["ad_title"],
        ad_text=row["ad_text"],
        ad_photo_url=row["ad_photo_url"],
        advertiser_id=row["advertiser_id"]
    )


@router.post("/{adId}/click", status_code=status.HTTP_204_NO_CONTENT)
async def record_ad_click(
    adId: UUID,
    payload: AdClickRequest,
    session: AsyncSession = Depends(get_session),
):
    success = await safe_record_click(adId, payload.client_id, session)
    if not success:
        raise HTTPException(
            status_code=409,
            detail="Cannot record click: either campaign is not active, limit reached, "
                   "campaign is deleted, or user never saw this ad."
        )
    return


async def safe_record_impression(
    campaign_id: UUID,
    client_id: UUID,
    session: AsyncSession
) -> bool:
    lock_stmt = (
        select(Campaign)
        .where(Campaign.campaign_id == campaign_id)
        .with_for_update()
    )
    locked_campaign = (await session.execute(lock_stmt)).scalar_one_or_none()
    if not locked_campaign:
        return False

    if locked_campaign.is_deleted:
        return False

    current_day = await get_current_day(session)
    if not (locked_campaign.start_date <= current_day <= locked_campaign.end_date):
        return False

    stmt_count = (
        select(func.count(distinct(AdEvent.client_id)))
        .where(AdEvent.campaign_id == campaign_id)
        .where(AdEvent.event_type == AdEventTypeEnum.IMPRESSION)
    )
    current_impr = (await session.execute(stmt_count)).scalar() or 0
    if current_impr >= locked_campaign.impressions_limit:
        return False

    check_stmt = (
        select(AdEvent)
        .where(AdEvent.campaign_id == campaign_id)
        .where(AdEvent.client_id == client_id)
        .where(AdEvent.event_type == AdEventTypeEnum.IMPRESSION)
    )
    exists = (await session.execute(check_stmt)).scalar_one_or_none()
    if exists:
        return True

    new_impr = AdEvent(
        campaign_id=campaign_id,
        client_id=client_id,
        event_type=AdEventTypeEnum.IMPRESSION,
        event_day=current_day
    )
    session.add(new_impr)
    await session.commit()
    return True


async def safe_record_click(
    campaign_id: UUID,
    client_id: UUID,
    session: AsyncSession
) -> bool:
    lock_stmt = (
        select(Campaign)
        .where(Campaign.campaign_id == campaign_id)
        .with_for_update()
    )
    locked_campaign = (await session.execute(lock_stmt)).scalar_one_or_none()
    if not locked_campaign:
        return False

    if locked_campaign.is_deleted:
        return False

    current_day = await get_current_day(session)
    if not (locked_campaign.start_date <= current_day <= locked_campaign.end_date):
        return False

    has_impression_stmt = (
        select(AdEvent)
        .where(AdEvent.campaign_id == campaign_id)
        .where(AdEvent.client_id == client_id)
        .where(AdEvent.event_type == AdEventTypeEnum.IMPRESSION)
    )
    has_impression = (await session.execute(has_impression_stmt)).scalar_one_or_none()
    if not has_impression:
        return False

    stmt_clicks = (
        select(func.count(distinct(AdEvent.client_id)))
        .where(AdEvent.campaign_id == campaign_id)
        .where(AdEvent.event_type == AdEventTypeEnum.CLICK)
    )
    current_clicks = (await session.execute(stmt_clicks)).scalar() or 0
    if current_clicks >= locked_campaign.clicks_limit:
        return False

    check_stmt = (
        select(AdEvent)
        .where(AdEvent.campaign_id == campaign_id)
        .where(AdEvent.client_id == client_id)
        .where(AdEvent.event_type == AdEventTypeEnum.CLICK)
    )
    clicked = (await session.execute(check_stmt)).scalar_one_or_none()
    if clicked:
        return True

    new_click = AdEvent(
        campaign_id=campaign_id,
        client_id=client_id,
        event_type=AdEventTypeEnum.CLICK,
        event_day=current_day
    )
    session.add(new_click)
    await session.commit()
    return True
