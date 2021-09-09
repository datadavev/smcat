import pytest
import tests.testserver
from twisted.internet import defer
import scrapy.crawler
import smcat.spiders.ldsitemap
import scrapy.http
import scrapy.settings


@pytest.fixture(scope="module")
def address():
    """
    Fire up a test server that serves content from the ./data folder
    """
    _server = tests.testserver.TestServer()
    _server.start()
    yield _server.getAddress()
    _server.stop()


@defer.inlineCallbacks
def test_robotstxt(address):
    url = f"{address}robots.txt"
    runner = scrapy.crawler.CrawlerRunner()
    settings = scrapy.settings.Settings(
        {
            "ITEM_PIPELINES": {"smcat.pipelines.ItemMemoryPipeline": 300},
            "SITEMAP_URLS": [
                url,
            ],
        }
    )

    crawler = scrapy.crawler.Crawler(smcat.spiders.ldsitemap.LdsitemapSpider, settings)
    yield runner.crawl(crawler, count_only=True)
    items = crawler.spider._item_memory
    assert len(items.kinds("RobotstxtItem")) == 1
    assert len(items.kinds("SitemapItem")) == 1
    assert len(items.kinds("SitemaplocItem")) == 3


@defer.inlineCallbacks
def test_simple_sitemap(address):
    url = f"{address}sm01.xml"
    runner = scrapy.crawler.CrawlerRunner()
    settings = scrapy.settings.Settings(
        {
            "ITEM_PIPELINES": {"smcat.pipelines.ItemMemoryPipeline": 300},
            "SITEMAP_URLS": [
                url,
            ],
        }
    )
    crawler = scrapy.crawler.Crawler(smcat.spiders.ldsitemap.LdsitemapSpider, settings)
    yield runner.crawl(crawler, count_only=True)
    items = crawler.spider._item_memory
    assert len(items.kinds("RobotstxtItem")) == 0
    assert len(items.kinds("SitemapItem")) == 1
    assert len(items.kinds("SitemaplocItem")) == 3


@defer.inlineCallbacks
def test_extended_sitemap(address):
    url = f"{address}sm02.xml"
    runner = scrapy.crawler.CrawlerRunner()
    settings = scrapy.settings.Settings(
        {
            "ITEM_PIPELINES": {"smcat.pipelines.ItemMemoryPipeline": 300},
            "SITEMAP_URLS": [
                url,
            ],
            "SITEMAP_ALTERNATE_LINKS": True,
        }
    )
    crawler = scrapy.crawler.Crawler(smcat.spiders.ldsitemap.LdsitemapSpider, settings)
    yield runner.crawl(crawler, count_only=False)
    items = crawler.spider._item_memory
    #for i in items.items:
    #    print(i)
    locs = items.kinds("SitemaplocItem")
    assert len(locs) == 4
    has_jsonld = False
    for loc in locs:
        if loc.get("link_type", "") == "application/ld+json":
            has_jsonld = True
            assert loc.get("url", "") == f"{address}content/ds01.jsonld"
    assert has_jsonld
