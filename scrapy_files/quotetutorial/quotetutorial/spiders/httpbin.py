# -*- coding: utf-8 -*-
import scrapy


class HttpbinSpider(scrapy.Spider):
    name = 'httpbin'
    allowed_domains = ['httpbin.org']
    start_urls = ['http://httpbin.org/post']
#默认是get请求，如果需要post请求的网页，更改start_requests
    def start_requests(self):
        yield scrapy.Request(url='http://httpbin.org/post',method='post',callback=self.parse_post)

    def parse(self, response):
        pass
    def parse_post(self,response):
        print('Hello',response.status)
