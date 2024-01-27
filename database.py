from sqlalchemy import create_engine, Column, String, DateTime, Boolean, ForeignKey, PrimaryKeyConstraint, JSON
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


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


def get_session(db_file='urls.db'):
    engine = create_engine(f'sqlite:///{db_file}')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create table if it doesn't exist
    Base.metadata.create_all(engine)

    return session
