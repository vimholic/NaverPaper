from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class VisitedUrl(Base):
    __tablename__ = 'visited_urls'

    url = Column(String, primary_key=True)
    date_added = Column(DateTime, default=datetime.utcnow)


def get_session(db_file='visited_urls.db'):
    # Connect to the SQLite database
    engine = create_engine(f'sqlite:///{db_file}')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create table if it doesn't exist
    Base.metadata.create_all(engine)

    return session
