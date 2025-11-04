# Standard library imports
from contextlib import contextmanager

# Third-party imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


class Database:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./urls.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base = declarative_base()

    @contextmanager
    def get_session(self):
        session_local = sessionmaker(bind=self.engine)
        session = session_local()
        self.Base.metadata.create_all(bind=self.engine)
        try:
            yield session
        finally:
            session.close()
