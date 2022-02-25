"""
Module for parsing sitemap.xml documents.

Chunks of this code based on https://github.com/scrapy/scrapy/blob/master/scrapy/utils/sitemap.py

This logic in here is a bit foobar since it's kind of half implemented from the scrapy
sitemap parser.

It needs to be modified to emit each type of thing encountered instead of just the leaves.
"""
import datetime
import types
import logging
import re
import struct
import io
import gzip
import urllib.parse
import lxml.etree
import requests
import functools
import dateutil.parser

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

L = logging.getLogger("sitemap")

XML_MEDIA_TYPES = [
    "text/xml",
    "application/xml",
]
SM_LOC = "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
SM_LASTMOD = "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod"
SM_PRIORITY = "{http://www.sitemaps.org/schemas/sitemap/0.9}priority"
SM_CHANGEFREQ = "{http://www.sitemaps.org/schemas/sitemap/0.9}changefreq"


@functools.cache
def _toDatetimeTZ(V):
    return dateutil.parser.isoparse(V)


# @deprecated('GzipFile.read1')
def read1(gzf, size=-1):
    return gzf.read1(size)


def gunzip(data):
    """Gunzip the given data and return as much data as possible.
    This is resilient to CRC checksum errors.
    """
    f = gzip.GzipFile(fileobj=io.BytesIO(data))
    output_list = []
    chunk = b"."
    while chunk:
        try:
            chunk = f.read1(8196)
            output_list.append(chunk)
        except (IOError, EOFError, struct.error):
            # complete only if there is some data, otherwise re-raise
            # see issue 87 about catching struct.error
            # some pages are quite small so output_list is empty and f.extrabuf
            # contains the whole page content
            if output_list or getattr(f, "extrabuf", None):
                try:
                    output_list.append(f.extrabuf[-f.extrasize :])
                finally:
                    break
            else:
                raise
    return b"".join(output_list)


def gzipMagicNumber(response):
    return response.content[:3] == b"\x1f\x8b\x08"


def isXmlResponse(response):
    if response.url.endswith(".xml"):
        return True
    content_type = response.headers.get("content-type", "")
    media_type = content_type.split(";", 1)
    L.debug("Content type: %s -> %s", content_type, media_type)
    if media_type[0] in XML_MEDIA_TYPES:
        return True
    return False


def regex(x):
    if isinstance(x, str):
        return re.compile(x)
    return x


def sitemapUrlsFromRobots(robots_text, base_url=None):
    """Return iterator over sitemap urls in robots_text"""
    for line in robots_text.splitlines():
        if line.lstrip().lower().startswith("sitemap:"):
            url = line.split(":", 1)[1].strip()
            yield urllib.parse.urljoin(base_url, url)


def iterloc(it):
    for d in it:
        ts = d.get(SM_LASTMOD, None)
        try:
            ts = _toDatetimeTZ(d.get(SM_LASTMOD, None))
        except:
            L.debug("Failed to parse %s", ts)
            pass
        d[SM_LASTMOD] = ts
        yield d


class SiteMapIterator(object):
    """
    Iterates over a single XML sitemap document.

    Yields a dictionary with keys as {namespace}element_name. If the
    element has attributes, then a dictionary is provided with
    attributes as keys and "@value" the value of the element, if any.
    """

    def __init__(self, xml_text):
        xmlp = lxml.etree.XMLParser(
            recover=True, remove_comments=True, resolve_entities=False
        )
        self._root = lxml.etree.fromstring(xml_text, parser=xmlp)
        rt = self._root.tag
        self.type = self._root.tag.split("}", 1)[1] if "}" in rt else rt

    def __iter__(self):
        for elem in self._root.getchildren():
            d = {}
            for el in elem.getchildren():
                tag = el.tag
                if len(el.keys()) > 0:
                    o = {}
                    for k, v in el.items():
                        o[k] = v
                    _v = el.text.strip() if el.text else None
                    if _v is not None:
                        o["@value"] = _v
                    d[tag] = o
                else:
                    d[tag] = el.text.strip() if el.text else ""
            if SM_LOC in d:
                yield d


class BaseTask:
    def __init__(self):
        pass

    def exec(self, **kwargs):
        raise NotImplementedError("BaseTask")

    def parseSitemap(self, response):
        return None


class RobotstxtTask(BaseTask):
    def exec(self, **kwargs):
        response = kwargs.get("response", None)
        if response is None:
            return
        for url in sitemapUrlsFromRobots(response.text, base_url=response.url):
            yield {"task": "sitemap", "body": {"url": url, "cb": self.parseSitemap}}


class SiteMap(object):
    def __init__(self, url, start_from: datetime.datetime = None, alt_rules=None):
        """
        Initialize a SiteMap object

        Args:
            url: The url of a sitemap xml or gzipped xml document
            start_from: Optional, entries with lastmod > start_from are returned
            alt_rules: Optional, list of (expression, callback) applied to each
              entry. If the expression (regexp string) matches the loc value for
              a url entry, then callback is called with the url structure

        """
        self.sitemap_url = url
        self.sitemap_alternate_links = False
        self.sitemap_rules = [("", "parseUrl")]
        self.sitemap_follow = [""]
        self.start_from = start_from
        self._session = requests.Session()
        self._cbs = []
        self._all_sitemaps = []  # list of all sitemaps visited
        if alt_rules is not None:
            for r, c in alt_rules:
                if isinstance(c, str):
                    c = getattr(self, c)
                self._cbs.append((regex(r), c))
        else:
            for r, c in self.sitemap_rules:
                if isinstance(c, str):
                    c = getattr(self, c)
                self._cbs.append((regex(r), c))
        self._follow = [regex(x) for x in self.sitemap_follow]

    def parseUrl(self, task):
        """Return an object given an entry"""
        return task
        # url = task.get("url", "")
        # return url

    def sitemapFilter(self, entries):
        """Override this to filter entries"""
        for entry in entries:
            yield entry

    def parseSitemap(self, response):
        self._all_sitemaps.append(response.url)
        if response.url.endswith("/robots.txt"):
            for url in sitemapUrlsFromRobots(response.text, base_url=response.url):
                yield {
                    "task": "robotsitemap",
                    "body": {"url": url, "cb": self.parseSitemap},
                }
        else:
            body = self.getSitemapBody(response)
            if body is None:
                L.warning("Ignoring invalid sitemap: %s", response.url)
                return
            s = SiteMapIterator(body)
            L.info("Sitemap type = %s", s.type)
            s_it = self.sitemapFilter(s)
            if s.type == "sitemapindex":
                for url in iterloc(s_it):
                    if any(x.search(url[SM_LOC]) for x in self._follow):
                        yield {
                            "task": "sitemapindex",
                            "body": {
                                "kind": "sitemap",
                                "url": url,
                                "cb": self.parseSitemap,
                                "source": response.history[0].url if response.history else response.url,
                            },
                        }
            elif s.type == "urlset":
                # recall that a url in a urlset is a structure containing loc (the url value)
                for url in iterloc(s_it):
                    for r, c in self._cbs:
                        if (
                            r.search(url[SM_LOC])
                            and self.start_from is None
                            or url[SM_LASTMOD] >= self.start_from
                        ):
                            req = {
                                "task": "url",
                                "body": {
                                    "kind": "url",
                                    "url": url,
                                    "cb": c,
                                    "source": response.history[0].url if response.history else response.url,
                                },
                            }
                            # L.debug("REQ: %s", req)
                            yield req

    def getSitemapBody(self, response):
        if isXmlResponse(response):
            return response.content
        elif gzipMagicNumber(response):
            return gunzip(response.content)
        elif response.url.endswith(".xml") or response.url.endswith(".xml.gz"):
            return response.content
        L.warning("getSitemapBody no xml: %s", response.url)

    def _scanItems(self, iter=None):
        if isinstance(iter, types.GeneratorType):
            for action in iter:
                task = action.get("task", None)
                # yield the action to be undertaken.
                # This will generally be ignored by the receiver
                yield action
                if task in ["sitemapindex", "robotsitemap"]:
                    # load a sitemap body from the provided url
                    cb = action["body"].pop("cb")
                    yield action["body"]
                    url = action["body"]["url"].get(SM_LOC)
                    r = self._session.get(url)
                    # default action is parseSitemap(r)
                    _iterator = cb(r)
                    for item in self._scanItems(_iterator):
                        yield item
                elif task == "url":
                    # Handle a single URL entry
                    cb = action["body"].pop("cb")
                    params = action["body"]
                    # default callback is parse({"url": url}), where url is a
                    # url structure parsed from a urlset. The parse()
                    # method just returns the structure, so by default we
                    # are just yielding the url structure here.
                    _iterator = cb(params)
                    for item in self._scanItems(_iterator):
                        yield (item)
            return
        yield iter

    def scanItems(self):
        response = self._session.get(self.sitemap_url)
        iter = self.parseSitemap(response)
        return self._scanItems(iter)

    def __iter__(self):
        for item in self.scanItems():
            L.debug(f"ITER: {item}")
            yield item


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    url = "http://localhost:18001/sm02.xml"
    sm = SiteMap(url)
    counter = 0
    for item in sm:  # .scanItems():
        counter += 1
        print(f"{counter:07d}: {item}")
