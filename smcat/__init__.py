"""
Implements a sitemap.xml parser for introspection
"""

import datetime
import logging
import sqlmodel
import smcat.sitemap
import smcat.models

_L = logging.getLogger("smcat")



def addTreeToDatabase(engine, tree, commit_batch=100):
    counter = 0
    keys = []
    with smcat.models.get_session(engine) as session:
        for item in tree:
            item_kind = item.get('kind')
            if item_kind == 'sitemap':
                _url = item.get('url', {}).get(smcat.sitemap.SM_LOC)
                if _url is None:
                    _L.warning("URL is required for a sitemap entry")
                    continue
                existing = (
                    session.query(smcat.models.SitemapIndex)
                        .filter(smcat.models.SitemapIndex.loc == _url)
                        .one_or_none()
                )
                if existing is None:
                    _i = item.get('url')
                    entry = smcat.models.SitemapIndex(
                        loc = _i.get(smcat.sitemap.SM_LOC),
                        lastmod = _i.get(smcat.sitemap.SM_LASTMOD),
                        source = item.get('source')
                    )
                    _L.info(entry)
                    session.add(entry)
                else:
                    _ = session.merge(existing)
                session.commit()
            elif item_kind == 'url':
                _url = item.get('url', {}).get(smcat.sitemap.SM_LOC)
                if _url is None:
                    _L.warning("URL is required for a sitemap entry")
                    return
                if _url in keys:
                    # Existing uncommitted entry
                    # Commit outstanding entries and proceed
                    session.commit()
                    keys = []
                else:
                    keys.append(_url)
                existing = (
                    session.query(smcat.models.SitemapEntry)
                        .filter(smcat.models.SitemapEntry.loc == _url)
                        .one_or_none()
                )
                if existing is None:
                    _i = item['url']
                    entry = smcat.models.SitemapEntry(
                        loc=_i.get(smcat.sitemap.SM_LOC),
                        priority=_i.get(smcat.sitemap.SM_PRIORITY),
                        lastmod=_i.get(smcat.sitemap.SM_LASTMOD),
                        changefreq=_i.get(smcat.sitemap.SM_CHANGEFREQ),
                        source=item.get("source")
                    )
                    _L.info(entry)
                    session.add(entry)
                else:
                    _ = session.merge(existing)
            counter += 1
            if counter % commit_batch == 0:
                session.commit()
                keys = []
                _L.debug("Added %s entries", counter)
        session.commit()


def loadSitemap(url, engine=None, commit_batch=100):
    tree = smcat.sitemap.SiteMap(url)
    if engine is not None:
        addTreeToDatabase(engine, tree, commit_batch=commit_batch)
    return tree
