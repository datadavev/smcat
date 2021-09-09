import logging
import scrapy
import urllib.parse
from scrapy.http import Request, XmlResponse
from scrapy.utils.gz import gunzip, gzip_magic_number

import smcat.items
import smcat.common
import smcat.sitemap

logger = logging.getLogger("LDSitemap")


def iterloc(it):
    for d in it:
        ts = d.get("lastmod", None)
        freq = d.get("changefreq", None)
        prio = d.get("priority", None)
        yield (d, d["loc"], ts, freq, prio)


def iterlocalt(d):
    if "alternate" in d:
        for link in d["alternate"]:
            yield (
                link["href"],
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
        logger.info("INIT")
        self.sitemap_urls = sitemap_urls
        logger.info("INIT sitemap_urls=%s", sitemap_urls)
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
        """
        Processing starts here. The list of urls to process is provided in the constructor
        or in the settings.

        The first step is processing the sitemap documents.

        Processing content referenced by sitemaps is handled by callbacks registered
        in this instance via SITEMAP_RULES.
        """
        for url in self.sitemap_urls:
            yield Request(url, self.parse_sitemapResponse, cb_kwargs={"parent": url})

    def sitemap_filter(self, entries):
        """This method can be used to filter sitemap entries by their
        attributes, for example, you can filter locs with lastmod greater
        than a given date (see docs).
        """
        for entry in entries:
            yield entry

    def process_robotstxt(self, response, t_mod=None, **kwargs):
        item = smcat.items.RobotstxtItem()
        item.set(
            source=response.url,
            time_mod=t_mod,
            time_retrieved=smcat.common.dtnow(),
            from_item=kwargs.get("from_item", None),
        )
        # yield an item describing the robots.txt
        yield item

        # yield new requests for the URLs found in the robots.txt
        for url in smcat.sitemap.sitemap_urls_from_robots(
            response.text, base_url=response.url
        ):
            yield Request(
                url,
                callback=self.parse_sitemapResponse,
                cb_kwargs={"source": response.url, "from_item": item["id"]},
            )

    def process_sitemap(self, response, t_mod=None, body=None, **kwargs):
        def _handle_loc(
            loc, from_item, last_mod, freq, prio, link_type=None, link_profile=None
        ):
            for r, c in self._cbs:
                if r.search(loc):
                    # Create a new request to retrieve the referenced item
                    if not self._count_only:
                        cb_kwargs = {
                            "from_item": from_item,
                            "loc_loc": loc,
                            "loc_lastmod": last_mod,
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

        # Handle processing of the sitemap document
        smitem = smcat.items.SitemapItem()
        smitem.set(
            source=response.url,
            time_mod=t_mod,
            time_retrieved=smcat.common.dtnow(),
            from_item=kwargs.get("from_item", None),
        )
        # Yield the sitemap item and continue further processing
        yield smitem

        # Process the sitemap document
        s = smcat.sitemap.Sitemap(body)
        it = self.sitemap_filter(s)

        # If this is a sitemap index, yield new requests to
        # retrieve the referenced sitemap documents
        if s.type == "sitemapindex":
            for (element, loc, ts, freq, prio) in iterloc(it):
                if any(x.search(loc) for x in self._follow):
                    yield Request(
                        loc,
                        callback=self.parse_sitemapResponse,
                        cb_kwargs={"source": response.url, "from_item": smitem["id"]},
                    )
            return
        if s.type == "urlset":
            # for each location found in the sitemap
            for (element, loc, ts, freq, prio) in iterloc(it):
                item = smcat.items.SitemaplocItem()
                item.set(
                    source=response.url,
                    from_item=smitem["id"],
                    time_retrieved=smcat.common.dtnow(),
                    url=loc,
                    time_loc=smcat.common.parseDatetimeString(ts),
                    time_mod=t_mod,
                    changefreq=freq,
                    priority=prio,
                )
                # yield an item describing the sitemap
                yield item
                # call the registered callbacks for the location found
                yield from _handle_loc(loc, item["id"], ts, freq, prio)

                # There may be multiple alternate links per loc entry
                # Examine those if requested and generate an item for the entry
                # and issue a request for the referenced content
                if self.follow_alternate_links:
                    for (loc, link_type, link_profile) in iterlocalt(element):
                        aitem = smcat.items.SitemaplocItem()
                        aitem.set(
                            source=item["source"],
                            from_item=item["id"],
                            time_retrieved=item["time_retrieved"],
                            url=loc,
                            time_loc=item["time_loc"],
                            time_mod=t_mod,
                            changefreq=freq,
                            priority=prio,
                            link_type=link_type,
                            link_profile=link_profile,
                        )
                        yield aitem
                        # call the registered callbacks for each location found
                        yield from _handle_loc(
                            loc,
                            item["id"],
                            ts,
                            freq,
                            prio,
                            link_type=link_type,
                            link_profile=link_profile,
                        )

    def parse_sitemapResponse(self, response, **kwargs):
        """
        Parse a response.

        Given a response, select appropriate process_* method to call

        Args:
            response:
            **kwargs:

        Returns:
            nothing
        """
        # get last-modified or set it to current time if not available
        t_mod = response.headers.get("Last-Modified", None)
        if t_mod is not None:
            if isinstance(t_mod, bytes):
                t_mod = t_mod.decode("utf-8")
            t_mod = smcat.common.parseDatetimeString(t_mod)

        media_type, charset = smcat.common.parseContentType(
            response.headers.get("Content-Type", None)
        )

        if media_type is None:
            logger.warning("Content type not provided for URL=%s", response.url)
            # Default to octet-stream
            # https://httpwg.org/specs/rfc7231.html#header.content-type
            media_type = "application/octet-stream"

        url_parsed = urllib.parse.urlparse(response.url)

        # Handle special case of a robots.txt URL which may contain
        # locations of sitemap(s) to be processed.
        if url_parsed.path.endswith("/robots.txt"):
            yield from self.process_robotstxt(response, t_mod)
            return

        # Is response for a sitemap?
        body = self._get_sitemap_body(response)
        if body is not None:
            yield from self.process_sitemap(response, t_mod, body=body, **kwargs)
            return
        logger.warning(
            "No sitemap body for url %s", response.url, extra={"spider": self}
        )

    def parse(
        self,
        response,
        from_item=None,
        loc_loc=None,
        loc_lastmod=None,
        loc_freq=None,
        loc_priority=None,
        loc_link_type=None,
        loc_link_profile=None,
        **kwargs
    ):
        """
        Handles parsing of documents other than sitemap pieces
        """
        # get last-modified or set it to current time if not available
        t_mod = response.headers.get("Last-Modified", None)
        if t_mod is not None:
            if isinstance(t_mod, bytes):
                t_mod = t_mod.decode("utf-8")
            t_mod = smcat.common.parseDatetimeString(t_mod)

        media_type, charset = smcat.common.parseContentType(
            response.headers.get("Content-type", None)
        )

        if media_type is None:
            logger.warning("Content type not provided for URL=%s", response.url)
            # Default to octet-stream
            # https://httpwg.org/specs/rfc7231.html#header.content-type
            media_type = "application/octet-stream"

        url_parsed = urllib.parse.urlparse(response.url)
        pass

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
        return None
