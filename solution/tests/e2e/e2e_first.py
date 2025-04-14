import pytest
import requests

BASE_URL = "http://backend:8080"


@pytest.fixture(scope="session")
def session():
    with requests.Session() as s:
        yield s


def check_validation_error(resp):
    assert resp.status_code == 422, f"Ожидали 422, получили {resp.status_code}"
    json_resp = resp.json()
    assert "detail" in json_resp, "Валидационная ошибка не содержит detail"


EXAMPLE_CLIENTS = [
    {
        "client_id": "21111111-1111-1111-1111-111111111111",
        "login": "test_client_login",
        "age": 25,
        "location": "Moscow",
        "gender": "MALE"
    },
    {
        "client_id": "32222222-2222-2222-2222-222222222222",
        "login": "another_client",
        "age": 32,
        "location": "Paris",
        "gender": "FEMALE"
    }
]

EXAMPLE_ADVERTISERS = [
    {
        "advertiser_id": "baaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "name": "Test Advertiser"
    },
    {
        "advertiser_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "name": "Second Advertiser"
    }
]

EXAMPLE_CAMPAIGN_CREATE = {
    "impressions_limit": 1000,
    "clicks_limit": 500,
    "cost_per_impression": 0.5,
    "cost_per_click": 2.0,
    "ad_title": "My Test Ad",
    "ad_text": "Buy our product!",
    "ad_photo_url": None,
    "start_date": 0,
    "end_date": 10,
    "targeting": {
        "gender": "MALE",
        "age_from": 0,
        "age_to": 100,
        "location": None
    }
}

EXAMPLE_CAMPAIGN_UPDATE = {
    "clicks_limit": 600,
    "ad_text": "Special discount today only!"
}

EXAMPLE_ML_SCORE = {
    "client_id": "11111111-1111-1111-1111-111111111111",
    "advertiser_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "score": 42
}


def test_01_upsert_clients(session):
    resp = session.post(f"{BASE_URL}/clients/bulk", json=EXAMPLE_CLIENTS)
    assert resp.status_code == 201, f"Ожидали 201, получили {resp.status_code}"
    json_resp = resp.json()
    assert isinstance(json_resp, list), "Ожидали список клиентов в ответе"
    assert len(json_resp) == len(EXAMPLE_CLIENTS), "Количество клиентов в ответе не совпадает"


def test_02_get_client_by_id(session):
    client_id = EXAMPLE_CLIENTS[0]["client_id"]
    resp = session.get(f"{BASE_URL}/clients/{client_id}")
    assert resp.status_code == 200, f"Ожидали 200, получили {resp.status_code}"
    json_resp = resp.json()
    assert json_resp["client_id"] == client_id, "ID клиента не совпадает"
    assert json_resp["login"] == EXAMPLE_CLIENTS[0]["login"], "Логин не совпадает"


def test_03_upsert_advertisers(session):
    resp = session.post(f"{BASE_URL}/advertisers/bulk", json=EXAMPLE_ADVERTISERS)
    assert resp.status_code == 201, f"Ожидали 201, получили {resp.status_code}"
    json_resp = resp.json()
    assert isinstance(json_resp, list), "Ожидали список рекламодателей в ответе"
    assert len(json_resp) == len(EXAMPLE_ADVERTISERS), "Количество рекламодателей в ответе не совпадает"


def test_04_get_advertiser_by_id(session):
    advertiser_id = EXAMPLE_ADVERTISERS[0]["advertiser_id"]
    resp = session.get(f"{BASE_URL}/advertisers/{advertiser_id}")
    assert resp.status_code == 200, f"Ожидали 200, получили {resp.status_code}"
    json_resp = resp.json()
    assert json_resp["advertiser_id"] == advertiser_id, "ID рекламодателя не совпадает"
    assert json_resp["name"] == EXAMPLE_ADVERTISERS[0]["name"], "Имя рекламодателя не совпадает"


def test_05_upsert_ml_score(session):
    resp = session.post(f"{BASE_URL}/ml-scores", json=EXAMPLE_ML_SCORE)
    assert resp.status_code == 201, f"Ожидали 201, получили {resp.status_code}"


CAMPAIGN_ID = None


def test_06_create_campaign(session):
    advertiser_id = EXAMPLE_ADVERTISERS[0]["advertiser_id"]
    resp = session.post(
        f"{BASE_URL}/advertisers/{advertiser_id}/campaigns",
        json=EXAMPLE_CAMPAIGN_CREATE
    )
    assert resp.status_code == 201, f"Ожидали 201, получили {resp.status_code}"
    json_resp = resp.json()
    assert "campaign_id" in json_resp, "В ответе нет campaign_id"
    global CAMPAIGN_ID
    CAMPAIGN_ID = json_resp["campaign_id"]
    assert json_resp["advertiser_id"] == advertiser_id, "advertiser_id не совпадает"


def test_07_get_campaign(session):
    advertiser_id = EXAMPLE_ADVERTISERS[0]["advertiser_id"]
    resp = session.get(f"{BASE_URL}/advertisers/{advertiser_id}/campaigns/{CAMPAIGN_ID}")
    assert resp.status_code == 200, f"Ожидали 200, получили {resp.status_code}"
    json_resp = resp.json()
    assert json_resp["campaign_id"] == CAMPAIGN_ID, "ID кампании не совпадает"
    assert json_resp["advertiser_id"] == advertiser_id, "ID рекламодателя не совпадает"


def test_08_get_ad_for_client(session):
    client_id = EXAMPLE_CLIENTS[0]["client_id"]
    resp = session.get(f"{BASE_URL}/ads", params={"client_id": client_id})
    assert resp.status_code == 200, f"Ожидали 200, получили {resp.status_code}"
    json_resp = resp.json()
    assert "ad_id" in json_resp, "Нет ad_id в ответе"
    assert "ad_title" in json_resp, "Нет ad_title в ответе"
    assert "advertiser_id" in json_resp, "Нет advertiser_id в ответе"


def test_09_record_ad_click(session):
    data = {
        "client_id": EXAMPLE_CLIENTS[0]["client_id"]
    }
    resp = session.post(f"{BASE_URL}/ads/{CAMPAIGN_ID}/click", json=data)
    assert resp.status_code == 204, f"Ожидали 204, получили {resp.status_code}"


def test_10_update_campaign(session):
    advertiser_id = EXAMPLE_ADVERTISERS[0]["advertiser_id"]
    resp = session.put(
        f"{BASE_URL}/advertisers/{advertiser_id}/campaigns/{CAMPAIGN_ID}",
        json=EXAMPLE_CAMPAIGN_UPDATE
    )
    assert resp.status_code == 200, f"Ожидали 200, получили {resp.status_code}"
    json_resp = resp.json()
    assert json_resp["clicks_limit"] == EXAMPLE_CAMPAIGN_UPDATE["clicks_limit"]
    assert json_resp["ad_text"] == EXAMPLE_CAMPAIGN_UPDATE["ad_text"]


def test_11_list_campaigns(session):
    advertiser_id = EXAMPLE_ADVERTISERS[0]["advertiser_id"]
    resp = session.get(f"{BASE_URL}/advertisers/{advertiser_id}/campaigns")
    assert resp.status_code == 200, f"Ожидали 200, получили {resp.status_code}"
    json_resp = resp.json()
    assert isinstance(json_resp, list), "Ожидали список в ответе"
    campaign_ids = [c["campaign_id"] for c in json_resp]
    assert CAMPAIGN_ID in campaign_ids, "Нашей кампании нет в списке"


def test_12_get_campaign_stats(session):
    resp = session.get(f"{BASE_URL}/stats/campaigns/{CAMPAIGN_ID}")
    assert resp.status_code == 200, f"Ожидали 200, получили {resp.status_code}"
    json_resp = resp.json()
    for key in ["impressions_count", "clicks_count", "conversion",
                "spent_impressions", "spent_clicks", "spent_total"]:
        assert key in json_resp, f"В ответе /stats/campaigns/{CAMPAIGN_ID} нет ключа {key}"


def test_13_get_campaign_daily_stats(session):
    resp = session.get(f"{BASE_URL}/stats/campaigns/{CAMPAIGN_ID}/daily")
    assert resp.status_code == 200, f"Ожидали 200, получили {resp.status_code}"
    json_resp = resp.json()
    assert isinstance(json_resp, list), "Ожидали список объектов"
    if json_resp:
        daily_stat = json_resp[0]
        for key in ["impressions_count", "clicks_count", "conversion",
                    "spent_impressions", "spent_clicks", "spent_total", "date"]:
            assert key in daily_stat, f"В объекте /daily stats нет ключа {key}"


def test_14_get_advertiser_campaigns_stats(session):
    advertiser_id = EXAMPLE_ADVERTISERS[0]["advertiser_id"]
    resp = session.get(f"{BASE_URL}/stats/advertisers/{advertiser_id}/campaigns")
    assert resp.status_code == 200, f"Ожидали 200, получили {resp.status_code}"
    json_resp = resp.json()
    for key in ["impressions_count", "clicks_count", "conversion",
                "spent_impressions", "spent_clicks", "spent_total"]:
        assert key in json_resp, f"Нет ключа {key} в ответе"


def test_15_get_advertiser_daily_stats(session):
    advertiser_id = EXAMPLE_ADVERTISERS[0]["advertiser_id"]
    resp = session.get(f"{BASE_URL}/stats/advertisers/{advertiser_id}/campaigns/daily")
    assert resp.status_code == 200, f"Ожидали 200, получили {resp.status_code}"
    json_resp = resp.json()
    assert isinstance(json_resp, list), "Ожидали список объектов"
    if json_resp:
        daily_stat = json_resp[0]
        for key in ["impressions_count", "clicks_count", "conversion",
                    "spent_impressions", "spent_clicks", "spent_total", "date"]:
            assert key in daily_stat, f"В объекте daily stats нет ключа {key}"


def test_16_advance_time(session):
    data = {
        "current_date": 2
    }
    resp = session.post(f"{BASE_URL}/time/advance", json=data)
    assert resp.status_code == 200, f"Ожидали 200, получили {resp.status_code}"
    json_resp = resp.json()
    assert "current_date" in json_resp, "Нет поля current_date"
    assert json_resp["current_date"] == 2, "Текущая дата не совпадает с ожидаемой"
