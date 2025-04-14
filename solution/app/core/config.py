from typing import Any, Literal, Optional

from pydantic_settings import BaseSettings


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"

    DOMAIN: str = "localhost"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    POSTGRES_HOST: Optional[str] = 'localhost'
    POSTGRES_PORT: Optional[int] = 5432
    POSTGRES_USERNAME: Optional[str] = 'postgres'
    POSTGRES_PASSWORD: Optional[str] = 'Version20'
    POSTGRES_DATABASE: Optional[str] = 'prod2'

    GPT_BASE: Optional[str] = 'REDACTED'
    GPT_API_KEY: Optional[str] = 'REDACTED'
    MODERATE_ADS: Optional[bool] = True

    AWS_KEY_ID: Optional[str] = 'REDACTED'
    AWS_ACCESS_KEY: Optional[str] = 'REDACTED'
    AWS_ENDPOINT_URL: Optional[str] = 'REDACTED'

    BOT_TOKEN: Optional[str] = 'REDACTED'

    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    class Config:
        extra = "allow"


settings = Settings()
