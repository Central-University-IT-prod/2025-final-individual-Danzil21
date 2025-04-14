import aiohttp
from pydantic import BaseModel, validator, field_validator
from typing import List, Optional
from enum import Enum

from sqlalchemy.util import await_only


class ClientGenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class AdClickRequest(BaseModel):
    client_id: str


class AdResponse(BaseModel):
    ad_id: str
    ad_title: str
    ad_text: str
    ad_photo_url: Optional[str]
    advertiser_id: str


class AdvertiserResponse(BaseModel):
    advertiser_id: str
    name: str


class AdvertiserUpsert(BaseModel):
    advertiser_id: str
    name: str


class ClientResponse(BaseModel):
    client_id: str
    login: str
    age: int
    location: str
    gender: str


class ClientUpsert(BaseModel):
    client_id: str
    login: str
    age: int
    location: str
    gender: ClientGenderEnum


class CampaignCreate(BaseModel):
    impressions_limit: int
    clicks_limit: int
    cost_per_impression: float
    cost_per_click: float
    ad_title: str
    ad_text: str
    ad_photo_url: Optional[str] = None
    start_date: int
    end_date: int

    class Targeting(BaseModel):
        gender: Optional[str] = None
        age_from: Optional[int] = None
        age_to: Optional[int] = None
        location: Optional[str] = None

    targeting: Targeting

    @field_validator("ad_photo_url")
    def validate_photo_url(cls, v):
        if v is not None and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("ad_photo_url must start with http:// or https://")
        return v


class CampaignUpdate(BaseModel):
    impressions_limit: Optional[int] = None
    clicks_limit: Optional[int] = None
    cost_per_impression: Optional[float] = None
    cost_per_click: Optional[float] = None
    ad_title: Optional[str] = None
    ad_text: Optional[str] = None
    ad_photo_url: Optional[str] = None
    start_date: Optional[int] = None
    end_date: Optional[int] = None

    class Targeting(BaseModel):
        gender: Optional[str] = None
        age_from: Optional[int] = None
        age_to: Optional[int] = None
        location: Optional[str] = None

    targeting: Optional[Targeting] = None


class CampaignResponse(BaseModel):
    campaign_id: str
    advertiser_id: str
    impressions_limit: int
    clicks_limit: int
    cost_per_impression: float
    cost_per_click: float
    ad_title: str
    ad_text: str
    ad_photo_url: Optional[str]
    start_date: int
    end_date: int

    class Targeting(BaseModel):
        gender: Optional[str] = None
        age_from: Optional[int] = None
        age_to: Optional[int] = None
        location: Optional[str] = None

    targeting: Targeting


class StatsResponse(BaseModel):
    impressions_count: int
    clicks_count: int
    conversion: float
    spent_impressions: float
    spent_clicks: float
    spent_total: float


class DailyStatsResponse(BaseModel):
    impressions_count: int
    clicks_count: int
    conversion: float
    spent_impressions: float
    spent_clicks: float
    spent_total: float
    date: int


class MLScoreSchema(BaseModel):
    client_id: str
    advertiser_id: str
    score: int


class TimeAdvanceRequest(BaseModel):
    current_date: int


class TimeAdvanceResponse(BaseModel):
    current_date: int


class UploadResponse(BaseModel):
    file_url: str


class AdvertisingPlatformClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if not self._session:
            raise RuntimeError("Client session is not initialized.")
        return self._session

    async def get_client_by_id(self, client_id: str) -> ClientResponse:
        url = f"{self.base_url}/clients/{client_id}"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return ClientResponse(**data)

    async def upsert_clients(self, clients: List[ClientUpsert]) -> List[ClientResponse]:
        url = f"{self.base_url}/clients/bulk"
        payload = [c.model_dump() for c in clients]
        async with self.session.post(url, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return [ClientResponse(**item) for item in data]

    async def get_advertiser_by_id(self, advertiser_id: str) -> AdvertiserResponse:
        url = f"{self.base_url}/advertisers/{advertiser_id}"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return AdvertiserResponse(**data)

    async def upsert_advertisers(self, advertisers: List[AdvertiserUpsert]) -> List[AdvertiserResponse]:
        url = f"{self.base_url}/advertisers/bulk"
        payload = [adv.model_dump() for adv in advertisers]
        async with self.session.post(url, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return [AdvertiserResponse(**item) for item in data]

    async def upsert_ml_score(self, ml_score: MLScoreSchema) -> str:
        url = f"{self.base_url}/ml-scores"
        async with self.session.post(url, json=ml_score.model_dump()) as resp:
            resp.raise_for_status()
            text = await resp.text()
            return text

    async def get_ad_for_client(self, client_id: str) -> AdResponse:
        url = f"{self.base_url}/ads"
        params = {"client_id": client_id}
        async with self.session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return AdResponse(**data)

    async def record_ad_click(self, ad_id: str, request: AdClickRequest) -> None:
        url = f"{self.base_url}/ads/{ad_id}/click"
        async with self.session.post(url, json=request.model_dump()) as resp:
            resp.raise_for_status()

    async def upload_photo(self, file_path: str) -> UploadResponse:
        url = f"{self.base_url}/upload/photo"
        with open(file_path, "rb") as f:
            form_data = aiohttp.FormData()
            form_data.add_field("file", f, filename=file_path, content_type="application/octet-stream")
            async with self.session.post(url, data=form_data) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return UploadResponse(**data)

    async def create_campaign(self, advertiser_id: str, campaign_data: CampaignCreate,
                              generate_text: Optional[bool] = False) -> CampaignResponse:
        url = f"{self.base_url}/advertisers/{advertiser_id}/campaigns"
        params = {}
        if generate_text:
            params["generate_text"] = True
        async with self.session.post(url, params=params, json=campaign_data.model_dump()) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return CampaignResponse(**data)

    async def list_campaigns(self, advertiser_id: str, page: int = 1, size: int = 10) -> List[CampaignResponse]:
        url = f"{self.base_url}/advertisers/{advertiser_id}/campaigns"
        params = {"page": page, "size": size}
        async with self.session.get(url, params=params) as resp:
            print(await resp.text())
            resp.raise_for_status()
            data = await resp.json()
            return [CampaignResponse(**item) for item in data]

    async def get_campaign(self, advertiser_id: str, campaign_id: str) -> CampaignResponse:
        url = f"{self.base_url}/advertisers/{advertiser_id}/campaigns/{campaign_id}"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return CampaignResponse(**data)

    async def update_campaign(self, advertiser_id: str, campaign_id: str, data: CampaignUpdate) -> CampaignResponse:
        url = f"{self.base_url}/advertisers/{advertiser_id}/campaigns/{campaign_id}"
        async with self.session.put(url, json=data.model_dump()) as resp:
            print(await resp.text())
            resp.raise_for_status()
            data = await resp.json()
            return CampaignResponse(**data)

    async def delete_campaign(self, advertiser_id: str, campaign_id: str) -> None:
        url = f"{self.base_url}/advertisers/{advertiser_id}/campaigns/{campaign_id}"
        async with self.session.delete(url) as resp:
            resp.raise_for_status()

    async def get_campaign_stats(self, campaign_id: str) -> StatsResponse:
        url = f"{self.base_url}/stats/campaigns/{campaign_id}"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return StatsResponse(**data)

    async def get_advertiser_campaigns_stats(self, advertiser_id: str) -> StatsResponse:
        url = f"{self.base_url}/stats/advertisers/{advertiser_id}/campaigns"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return StatsResponse(**data)

    async def get_campaign_daily_stats(self, campaign_id: str) -> List[DailyStatsResponse]:
        url = f"{self.base_url}/stats/campaigns/{campaign_id}/daily"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return [DailyStatsResponse(**item) for item in data]

    async def get_advertiser_daily_stats(self, advertiser_id: str) -> List[DailyStatsResponse]:
        url = f"{self.base_url}/stats/advertisers/{advertiser_id}/campaigns/daily"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return [DailyStatsResponse(**item) for item in data]

    async def advance_day(self, request_data: TimeAdvanceRequest) -> TimeAdvanceResponse:
        url = f"{self.base_url}/time/advance"
        async with self.session.post(url, json=request_data.model_dump()) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return TimeAdvanceResponse(**data)
