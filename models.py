# Standard library imports
from datetime import datetime

# Third-party imports
from sqlalchemy import (
    Column, String, DateTime, Boolean, ForeignKey, PrimaryKeyConstraint, JSON
)
from sqlalchemy.orm import relationship

# Local imports
from database import Database

db = Database()
Base = db.Base


class CampaignUrl(Base):
    __tablename__ = 'campaign_urls'

    url = Column(String, primary_key=True)
    date_added = Column(DateTime, default=datetime.now())
    is_available = Column(Boolean, default=True)


class UrlVisit(Base):
    __tablename__ = 'url_visits'

    url = Column(String, ForeignKey('campaign_urls.url'))
    user_id = Column(String)
    visited_at = Column(DateTime)
    campaign_url = relationship("CampaignUrl")
    __table_args__ = (
        PrimaryKeyConstraint('url', 'user_id'),
    )


class User(Base):
    __tablename__ = "user"

    user_id = Column(String, primary_key=True)
    storage_state = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.now())
