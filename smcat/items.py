# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import smcat.common


def serializeDateTime(dt):
    return smcat.common.datetimeToJsonStr(dt)


class DocumentItem(scrapy.Item):
    """
    Attributes:
        kind: type name of this item
        time_retrieved: When the item was generated
        source: URL of the document leading to this item
        url: URL of the document this item is about
        time_mod: Timestamp reported in HTTP response Last-Modified header, if available

    """

    id = scrapy.Field()
    kind = scrapy.Field()
    time_retrieved = scrapy.Field(serializer=serializeDateTime)
    from_item = scrapy.Field()
    source = scrapy.Field()
    url = scrapy.Field()
    time_mod = scrapy.Field(serializer=serializeDateTime)

    def __init__(self):
        super().__init__()
        self.set(kind=self.name())
        self.set(id=smcat.common.getId())

    def setV(self, k, v, allow_none=False):
        if v is None and not allow_none:
            return
        self[k] = v

    def set(self, allow_none=False, **kwargs):
        for k, v in kwargs.items():
            if v is None and not allow_none:
                continue
            self[k] = v

    def name(self):
        return self.__class__.__name__


class RobotstxtItem(DocumentItem):
    """
    Describes a robots.txt document
    """

    pass


class SitemapItem(DocumentItem):
    """
    Describes a sitemap.xml document
    """

    pass


class SitemaplocItem(DocumentItem):
    """
    Properties of a document found by navigating from a sitemap loc entry.

    Attributes:
        time_loc: Timestamp in sitemap lastmod value, if available
        link_type: Type value from link, if available
        link_profile: Profile value from link, if available
        changefreq: String value of the changefreq element, if available
        priority: Value of the priority element, if available
    """

    time_loc = scrapy.Field(serializer=serializeDateTime)
    link_type = scrapy.Field()
    link_profile = scrapy.Field()
    changefreq = scrapy.Field()
    priority = scrapy.Field()


class JsonldItem(DocumentItem):
    # Time taken to retrieve the JsonLD, ms
    elapsed = scrapy.Field()
    # JsonLD content retrieved from a URL
    jsonld = scrapy.Field()
