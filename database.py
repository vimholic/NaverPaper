from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class CampaignUrl(Base):
    __tablename__ = 'campaign_urls'

    url = Column(String, primary_key=True)
    date_added = Column(DateTime, default=datetime.utcnow)


class UrlVisit(Base):
    __tablename__ = 'url_visits'

    url = Column(String, ForeignKey('campaign_urls.url'))
    user_id = Column(String)
    visited_at = Column(DateTime)

    campaign_url = relationship("CampaignUrl")

    __table_args__ = (
        PrimaryKeyConstraint('url', 'user_id'),
    )


def get_session(db_file='urls.db'):
    # Connect to the SQLite database
    engine = create_engine(f'sqlite:///{db_file}')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create table if it doesn't exist
    Base.metadata.create_all(engine)

    return session
