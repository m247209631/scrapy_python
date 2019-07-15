# -*- coding: utf-8 -*-
import scrapy
from quotetutorial.items import QuoteItem

class QuotesSpider(scrapy.Spider):#Spider的父类默认调用了start_requests()
    name = 'quotes'
    #当 OffsiteMiddleware 启用时，如果能匹配allowed_domains，则继续进行爬取，不能匹配则抛弃
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['http://quotes.toscrape.com/']

    def parse(self, response):
        # print(response.text)
        quotes = response.css('.quote')
        for quote in quotes:
            item = QuoteItem()
            text = quote.css('.text::text').extract_first()
            author = quote.css('.author::text').extract_first()
            tags = quote.css('.tag.tag::text').extract()#因为tag有多个，所以和上面的不太一样，extract()会把所有的都查找出来
            item['text'] = text
            item['author'] = author
            item['tags'] = tags
            yield item

        next = response.css('.pager .next a::attr(href)').extract_first()
        url = response.urljoin(next)#补全整个url链接
        yield scrapy.Request(url=url,callback=self.parse)
