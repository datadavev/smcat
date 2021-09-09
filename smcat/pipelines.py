# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class SmcatPipeline:
    def process_item(self, item, spider):
        return item


class ItemMemoryPipeline:
    '''
    Simple in memory pipeline that adds itself to the calling spider.
    Only used for testing.
    '''
    def __init__(self):
        self.ids_seen = set()

    def open_spider(self,spider):
        # hack to make this collection of items available from the spider
        # used for testing purposes.
        spider._item_memory = self
        self.items = []

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        self.items.append(item)
        return item

    def kinds(self, kind):
        res = []
        for i in self.items:
            if i.get('kind', '') == kind:
                res.append(i)
        return res

