import contextlib
import sqlmodel
from . import sitemap

SitemapIndex = sitemap.SitemapIndex
SitemapEntry = sitemap.SitemapEntry


def init_db(database_url):
    engine = sqlmodel.create_engine(database_url)
    sqlmodel.SQLModel.metadata.create_all(engine)
    return engine

@contextlib.contextmanager
def get_session(engine):
    session = sqlmodel.Session(engine)
    try:
        yield session
    finally:
        session.close()
