import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
from api.routes.ads import safe_record_impression, safe_record_click
from api.database.models.models import Campaign, AdEvent, AdEventTypeEnum


@pytest.mark.asyncio
async def test_safe_record_impression_success():
    mock_session = AsyncMock()

    mock_campaign = Campaign()
    mock_campaign.is_deleted = False
    mock_campaign.start_date = 0
    mock_campaign.end_date = 10
    mock_campaign.impressions_limit = 2

    campaign_id = UUID("11111111-1111-1111-1111-111111111111")
    client_id = UUID("22222222-2222-2222-2222-222222222222")

    mock_result_lock = MagicMock()
    mock_result_lock.scalar_one_or_none.return_value = mock_campaign

    mock_result_count = MagicMock()
    mock_result_count.scalar.return_value = 0

    mock_result_check = MagicMock()
    mock_result_check.scalar_one_or_none.return_value = None

    mock_session.execute.side_effect = [
        mock_result_lock,
        mock_result_count,
        mock_result_check
    ]

    async def mock_get_current_day(*args, **kwargs):
        return 1

    original_get_current_day = safe_record_impression.__globals__["get_current_day"]
    safe_record_impression.__globals__["get_current_day"] = mock_get_current_day

    result = await safe_record_impression(campaign_id, client_id, mock_session)
    assert result is True, "Ожидаем True, если все условия соблюдены"
    mock_session.commit.assert_awaited_once()

    safe_record_impression.__globals__["get_current_day"] = original_get_current_day


@pytest.mark.asyncio
async def test_safe_record_impression_campaign_not_found():
    mock_session = AsyncMock()

    mock_result_lock = MagicMock()
    mock_result_lock.scalar_one_or_none.return_value = None
    mock_session.execute.side_effect = [mock_result_lock]

    campaign_id = UUID("33333333-3333-3333-3333-333333333333")
    client_id = UUID("44444444-4444-4444-4444-444444444444")

    result = await safe_record_impression(campaign_id, client_id, mock_session)
    assert result is False
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_safe_record_impression_already_deleted():
    mock_session = AsyncMock()
    mock_campaign = Campaign()
    mock_campaign.is_deleted = True

    mock_result_lock = MagicMock()
    mock_result_lock.scalar_one_or_none.return_value = mock_campaign
    mock_session.execute.side_effect = [mock_result_lock]

    campaign_id = UUID("55555555-5555-5555-5555-555555555555")
    client_id = UUID("66666666-6666-6666-6666-666666666666")

    result = await safe_record_impression(campaign_id, client_id, mock_session)
    assert result is False
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_safe_record_impression_limit_reached():
    mock_session = AsyncMock()
    mock_campaign = Campaign()
    mock_campaign.is_deleted = False
    mock_campaign.start_date = 0
    mock_campaign.end_date = 10
    mock_campaign.impressions_limit = 1

    mock_result_lock = MagicMock()
    mock_result_lock.scalar_one_or_none.return_value = mock_campaign

    mock_result_count = MagicMock()
    mock_result_count.scalar.return_value = 1

    mock_session.execute.side_effect = [
        mock_result_lock,
        mock_result_count
    ]

    async def mock_get_current_day(*args, **kwargs):
        return 0

    original_get_current_day = safe_record_impression.__globals__["get_current_day"]
    safe_record_impression.__globals__["get_current_day"] = mock_get_current_day

    campaign_id = UUID("77777777-7777-7777-7777-777777777777")
    client_id = UUID("88888888-8888-8888-8888-888888888888")

    result = await safe_record_impression(campaign_id, client_id, mock_session)
    assert result is False
    mock_session.commit.assert_not_awaited()

    safe_record_impression.__globals__["get_current_day"] = original_get_current_day


@pytest.mark.asyncio
async def test_safe_record_click_success():
    """
    Кампания существует, не удалена, лимит кликов не достигнут,
    у клиента уже был IMPRESSION, а клик ещё не зарегистрирован — функция возвращает True.
    """
    mock_session = AsyncMock()
    mock_campaign = Campaign()
    mock_campaign.is_deleted = False
    mock_campaign.start_date = 0
    mock_campaign.end_date = 10
    mock_campaign.clicks_limit = 5

    mock_result_lock = MagicMock()
    mock_result_lock.scalar_one_or_none.return_value = mock_campaign

    mock_result_impression = MagicMock()
    mock_result_impression.scalar_one_or_none.return_value = "some_impression"

    mock_result_clicks = MagicMock()
    mock_result_clicks.scalar.return_value = 2

    mock_result_check = MagicMock()
    mock_result_check.scalar_one_or_none.return_value = None

    mock_session.execute.side_effect = [
        mock_result_lock,
        mock_result_impression,
        mock_result_clicks,
        mock_result_check
    ]

    async def mock_get_current_day(*args, **kwargs):
        return 2

    original_get_current_day = safe_record_click.__globals__["get_current_day"]
    safe_record_click.__globals__["get_current_day"] = mock_get_current_day

    campaign_id = UUID("11111111-1111-1111-1111-111111111111")
    client_id = UUID("22222222-2222-2222-2222-222222222222")

    result = await safe_record_click(campaign_id, client_id, mock_session)
    assert result is True
    mock_session.commit.assert_awaited()
    safe_record_click.__globals__["get_current_day"] = original_get_current_day


@pytest.mark.asyncio
async def test_safe_record_click_no_impression():
    """Если у клиента нет IMPRESSION, функция должна вернуть False."""
    mock_session = AsyncMock()
    mock_campaign = Campaign()
    mock_campaign.is_deleted = False
    mock_campaign.start_date = 0
    mock_campaign.end_date = 10
    mock_campaign.clicks_limit = 5

    mock_result_lock = MagicMock()
    mock_result_lock.scalar_one_or_none.return_value = mock_campaign

    mock_result_impression = MagicMock()
    mock_result_impression.scalar_one_or_none.return_value = None

    mock_session.execute.side_effect = [
        mock_result_lock,
        mock_result_impression,
    ]

    async def mock_get_current_day(*args, **kwargs):
        return 2

    original_get_current_day = safe_record_click.__globals__["get_current_day"]
    safe_record_click.__globals__["get_current_day"] = mock_get_current_day

    campaign_id = UUID("33333333-3333-3333-3333-333333333333")
    client_id = UUID("44444444-4444-4444-4444-444444444444")

    result = await safe_record_click(campaign_id, client_id, mock_session)
    assert result is False
    mock_session.commit.assert_not_awaited()
    safe_record_click.__globals__["get_current_day"] = original_get_current_day
