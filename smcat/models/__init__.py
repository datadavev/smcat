import contextlib
import sqlalchemy.orm
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


def mostRecentEntry(engine)->SitemapEntry:
    """Get the most recent url entry
    """
    with get_session(engine) as session:
        statement = (sqlmodel.select(SitemapEntry)
                     .order_by(SitemapEntry.lastmod.desc()))
        return session.exec(statement).first()


def getSitemapRoots(engine):
    with get_session(engine) as session:
        statement = ("select distinct source from sitemapindex "
                     "where source not in "
                     "(select distinct loc from sitemapindex)")
        return session.exec(statement).all()


def changedSince(engine, dtlast):
    with get_session(engine) as session:
        statement = (sqlmodel.select(SitemapEntry)
                     .where(SitemapEntry.lastmod > dtlast)
                     .order_by(SitemapEntry.lastmod.desc()))
        for entry in session.exec(statement):
            yield entry
