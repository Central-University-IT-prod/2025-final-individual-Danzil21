import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    Float, TIMESTAMP, func, BigInteger, Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class ClientGenderEnum(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class TargetingGenderEnum(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    ALL = "ALL"


class AdEventTypeEnum(str, enum.Enum):
    IMPRESSION = "IMPRESSION"
    CLICK = "CLICK"


class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    login = Column(String(64), nullable=False, index=True)
    age = Column(Integer, nullable=True, index=True)
    location = Column(String, nullable=True, index=True)
    gender = Column(Enum(ClientGenderEnum), nullable=True, index=True)

    ml_scores = relationship("MLScore", back_populates="client")
    ad_events = relationship("AdEvent", back_populates="client")


class Advertiser(Base):
    __tablename__ = "advertisers"

    advertiser_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False, index=True)

    ml_scores = relationship("MLScore", back_populates="advertiser")
    campaigns = relationship("Campaign", back_populates="advertiser")


class MLScore(Base):
    __tablename__ = "ml_scores"

    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), primary_key=True, index=True)
    advertiser_id = Column(UUID(as_uuid=True), ForeignKey("advertisers.advertiser_id"), primary_key=True, index=True)
    score = Column(Integer, nullable=False, index=True)

    client = relationship("Client", back_populates="ml_scores")
    advertiser = relationship("Advertiser", back_populates="ml_scores")


class Campaign(Base):
    __tablename__ = "campaigns"

    campaign_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    advertiser_id = Column(UUID(as_uuid=True), ForeignKey("advertisers.advertiser_id"), nullable=False)
    impressions_limit = Column(Integer, nullable=False, index=True)
    clicks_limit = Column(Integer, nullable=False, index=True)
    cost_per_impression = Column(Float, nullable=False, index=True)
    cost_per_click = Column(Float, nullable=False, index=True)
    ad_title = Column(String, nullable=False)
    ad_photo_url = Column(String)
    ad_text = Column(Text, nullable=False)
    start_date = Column(Integer, nullable=False, index=True)
    end_date = Column(Integer, nullable=False, index=True)

    target_gender = Column(Enum(TargetingGenderEnum), nullable=True, index=True)
    target_age_from = Column(Integer, nullable=True, index=True)
    target_age_to = Column(Integer, nullable=True, index=True)
    target_location = Column(String, nullable=True, index=True)

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    create_date = Column(DateTime, default=datetime.utcnow, nullable=True, index=True)

    advertiser = relationship("Advertiser", back_populates="campaigns")
    ad_events = relationship("AdEvent", back_populates="campaign")

    @property
    def targeting(self):
        return {
            "gender": self.target_gender,
            "age_from": self.target_age_from,
            "age_to": self.target_age_to,
            "location": self.target_location,
        }


class AdEvent(Base):
    __tablename__ = "ad_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.campaign_id"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True)
    event_type = Column(Enum(AdEventTypeEnum), nullable=False, index=True)
    event_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_day = Column(Integer, nullable=False, index=True)

    campaign = relationship("Campaign", back_populates="ad_events")
    client = relationship("Client", back_populates="ad_events")


class SystemTime(Base):
    __tablename__ = "system_time"

    id = Column(Integer, primary_key=True, autoincrement=True)
    current_date = Column(Integer, nullable=False)


class BotUser(Base):
    __tablename__ = "bot_users"

    user_id = Column(BigInteger, primary_key=True, unique=True)
    date = Column(TIMESTAMP(timezone=True), default=func.now())
    advertiser_id = Column(UUID(as_uuid=True), ForeignKey("advertisers.advertiser_id"))
    advertiser_name = Column(String)
