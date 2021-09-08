import logging
import scrapy
from scrapy.http import Request, XmlResponse
from scrapy.utils.gz import gunzip, gzip_magic_number

import smcat.items
import smcat.common
import smcat.sitemap

logger = logging.getLogger("LDSitemap")


def iterloc(it, alt=False):
    for d in it:
        ts = d.get("lastmod", None)
        freq = d.get("changefreq", None)
        prio = d.get("priority", None)
        yield (d["loc"], ts, freq, prio, None, None)

        # Also consider alternate URLs (html:link rel="alternate")
        if alt and "alternate" in d:
            for link in d["alternate"]:
                yield (
                    link["href"],
                    ts,
                    freq,
                    prio,
                    link.get("type"),
                    link.get("profile"),
                )


class LdsitemapSpider(scrapy.Spider):
    # name of this spider
    name = "LDSitemap"

    def __init__(
        self,
        *a,
        sitemap_urls=(),
        sitemap_rules=None,
        sitemap_follow=None,
        follow_alternate_links=False,
        **kw
    ):
        super().__init__(*a, **kw)
        logging.info("INIT")
        self.sitemap_urls = sitemap_urls
        logging.info("INIT sitemap_urls=%s", sitemap_urls)
        # list of regex,parser applied to each loc entry found in a sitemap
        if sitemap_rules is None:
            sitemap_rules = [("", "parse")]
        # List of regex's to match on the sitemap urls to follow
        if sitemap_follow is None:
            sitemap_follow = [""]
        # Follow alternate links found in a loc entry?
        self.follow_alternate_links = follow_alternate_links

        self._cbs = []
        for r, c in sitemap_rules:
            if isinstance(c, str):
                c = getattr(self, c)
            self._cbs.append((smcat.common.regex(r), c))
        self._follow = [smcat.common.regex(x) for x in sitemap_follow]
        urls = kw.get("sitemap_urls", None)
        if not urls is None:
            self.sitemap_urls = urls.split(" ")
        # If set, then don't download the target
        self._count_only = kw.get("count_only", False)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        logger.info("FROM_CRAWLER")
        settings = crawler.settings
        urls = settings.get("SITEMAP_URLS", [])
        if isinstance(urls, str):
            urls = urls.split(" ")
        spargs = {
            "sitemap_urls": urls,
            "sitemap_rules": settings.get(
                "SITEMAP_RULES",
                [
                    ("", "parse"),
                ],
            ),
            "sitemap_follow": settings.get(
                "SITEMAP_FOLLOW",
                [
                    "",
                ],
            ),
            "follow_alternate_links": settings.get("SITEMAP_ALTERNATE_LINKS", False),
        }
        kwargs.update(spargs)
        return cls(*args, **kwargs)

    def start_requests(self):
        for url in self.sitemap_urls:
            yield Request(url, self._parse_sitemap, cb_kwargs={"parent": url})

    def sitemap_filter(self, entries):
        """This method can be used to filter sitemap entries by their
        attributes, for example, you can filter locs with lastmod greater
        than a given date (see docs).
        """
        for entry in entries:
            yield entry

    def _parse_sitemap(self, response, **kwargs):
        t_mod = response.headers.get("Last-Modified", None)
        if t_mod is not None:
            if isinstance(t_mod, bytes):
                t_mod = t_mod.decode("utf-8")
            t_mod = smcat.common.parseDatetimeString(t_mod)
        if response.url.endswith("/robots.txt"):
            item = smcat.items.RobotstxtItem()
            item.set(
                source=response.url, time_mod=t_mod, time_retrieved=smcat.common.dtnow()
            )
            yield item
            for url in smcat.sitemap.sitemap_urls_from_robots(
                response.text, base_url=response.url
            ):
                yield Request(
                    url,
                    callback=self._parse_sitemap,
                    cb_kwargs={"parent": response.url},
                )
        else:
            body = self._get_sitemap_body(response)
            if body is None:
                logger.warning(
                    "Ignoring invalid sitemap: %(response)s",
                    {"response": response},
                    extra={"spider": self},
                )
                return
            item = smcat.items.SitemapItem()
            item.set(
                source=kwargs.get("parent", None),
                time_mod=t_mod,
                time_retrieved=smcat.common.dtnow(),
            )
            yield item

            s = smcat.sitemap.Sitemap(body)
            it = self.sitemap_filter(s)

            if s.type == "sitemapindex":
                for (loc, ts, freq, prio, l_type, l_pro) in iterloc(
                    it, self.follow_alternate_links
                ):
                    if any(x.search(loc) for x in self._follow):
                        yield Request(
                            loc,
                            callback=self._parse_sitemap,
                            cb_kwargs={"parent": response.url},
                        )
            elif s.type == "urlset":
                for (loc, ts, freq, prio, link_type, link_profile) in iterloc(
                    it, self.follow_alternate_links
                ):
                    for r, c in self._cbs:
                        if r.search(loc):
                            ts = smcat.common.parseDatetimeString(ts)
                            item = smcat.items.SitemaplocItem()
                            item.set(
                                source=response.url,
                                time_retrieved=smcat.common.dtnow(),
                                url=loc,
                                time_loc=ts,
                                time_mod=t_mod,
                                changefreq=freq,
                                priority=prio,
                                link_type=link_type,
                                link_profile=link_profile,
                            )
                            yield item
                            if not self._count_only:
                                cb_kwargs = {
                                    "loc_loc": loc,
                                    "loc_lastmod": ts,
                                    "loc_freq": freq,
                                    "loc_priority": prio,
                                    "loc_link_type": link_type,
                                    "loc_link_profile": link_profile,
                                }
                                req = Request(
                                    loc,
                                    callback=c,
                                    flags=[
                                        self._count_only,
                                    ],
                                    cb_kwargs=cb_kwargs,
                                )
                                yield req
                            break

    def _get_sitemap_body(self, response):
        """Return the sitemap body contained in the given response,
        or None if the response is not a sitemap.
        """
        if isinstance(response, XmlResponse):
            return response.body
        elif gzip_magic_number(response):
            return gunzip(response.body)
        # actual gzipped sitemap files are decompressed above ;
        # if we are here (response body is not gzipped)
        # and have a response for .xml.gz,
        # it usually means that it was already gunzipped
        # by HttpCompression middleware,
        # the HTTP response being sent with "Content-Encoding: gzip"
        # without actually being a .xml.gz file in the first place,
        # merely XML gzip-compressed on the fly,
        # in other word, here, we have plain XML
        elif response.url.endswith(".xml") or response.url.endswith(".xml.gz"):
            return response.body
