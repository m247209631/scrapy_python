# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem
import pymongo
class TextPipeline(object):
    def __init__(self,):
        self.limit = 50
    def process_item(self, item, spider):
        #把item保存到数据库中，使用pipline
        if item['text']:
            if len(item['text'])> self.limit:
                item['text'] = item['text'][0:self.limit].rstrip() + '...'
                return item
        else:
            return DropItem('Missing Text')#如果item不存在，抛出异常
        return item

class MongoPipeline(object):
    def __init__(self,mongo_url,mongo_db):
        self.mongo_url = mongo_url
        self.mongo_db = mongo_db

    @classmethod   #这里是一个类方法
    def from_crawler(cls,crawler):
        return cls(mongo_url=crawler.settings.get('MONGO_URL'),mongo_db=crawler.settings.get('MONGO_DB'))

    def open_spider(self,spider):
        self.client = pymongo.MongoClient(self.mongo_url)
        self.db = self.client[self.mongo_db]   #这里是中括号[]
    def process_item(self,item,spider):
        name = item.__class__.__name__
        self.db[name].insert(dict(item))
        return item
    def close_spider(self,spider):
        self.client.close()    #关闭MongoDB，释放内存
