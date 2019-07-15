# -*- coding: utf-8 -*-
import scrapy

#通过-a 往里面传入参数
class BaiduSpider(scrapy.Spider):
    name = 'baidu'
    allowed_domains = ['www.baidu.com']
    start_urls = ['http://www.baidu.com/']

    #默认情况下是start_requests调用了make_requests_from_url，可看原码，而这里如果有重写了start_requests，则就不再调用
    def start_requests(self):
        yield scrapy.Request(url='http://www.baidu.com',callback=self.parse_index)
    #参数是url，返回request,callback默认为parse方法
    def make_requests_from_url(self, url):
        return scrapy.Request(url=url,callback=self.parse_index)
    def parse(self, response):
        pass

    def parse_index(self,response):
        # print('Baidu',response.status)
        self.logger.info('HELLO',response.status)