import requests
from urllib.parse import urlencode
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
import pymongo
from lxml.etree import XMLSyntaxError
from config import *  #从config导入的时候会有红线，不知道为什么，改成WeixinArticles.config之后没有红线了

client = pymongo.MongoClient(MONGO_URI)
db = client[MONGO_DB]  #注意是用[] ，不是()
base_url = 'https://weixin.sogou.com/weixin?{query}'
#获取代理的接口
proxy = None

#cookies是用来设置登录信息的，有过期时间，需要更新
headers = {
'Cookie':'usid=OL5rI7SsNrPIJEok; IPLOC=CN1100; SUV=007C8ED4DF483D325CFCEFD6C2516276; wuid=AAGpzqbyJwAAAAqPMnC+MwIAkwA=; front_screen_resolution=1920*1080; FREQUENCY=1560080342811_2; LSTMV=110%2C17; LCLKINT=3339; CXID=8CD9FD29441784EBD2AA122A7BF13989; SUID=8BBDBA1B5E68860A5C56E387000AB0E7; ABTEST=8|1561786131|v1; weixinIndexVisited=1; JSESSIONID=aaaHeTF3GCWdpervjDiRw; PHPSESSID=djkt8emb7t7d8b83mcb6mqvkl2; SNUID=D056E26416139B63692388ED179201EF; sct=9',
'Host':'weixin.sogou.com',
'Upgrade-Insecure-Requests': '1',
'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'
}

def get_proxy():
    try:
        response = requests.get(PROXY_POOL_URL)
        if response.status_code == 200:
            # print(response.text)
            return response.text
        return None
    except ConnectionError:
        return None

#count设置请求次数
def get_html(url,count=1):
    #打印调制信息
    print('Crawling',url)
    print('Trying Count',count)

    #设置全局变量
    global proxy
    # print(proxy)
    if count >= MAX_COUNT:
        print('Tried Too Many Counts')
        return None
    try:
        #增加是否有代理的判断,如果有代理，使用代理，如果没有，则正常请求
        if proxy:
            proxies = {
                'http': 'http://' + proxy
            }
            #requests会默认处理302的跳转，使用allow_redirects = False，不让它默认处理跳转
            response = requests.get(url,allow_redirects=False,headers = headers,proxies=proxies)
            print(proxies)
        else:
            response = requests.get(url,allow_redirects=False, headers=headers)
            print(response.status_code)
            # print(response.text)
        if response.status_code == 200:
            return response.text
        if response.status_code == 302:
            #need Proxy
            print(response.status_code)
            #使用代理
            proxy = get_proxy()
            #判断代理
            if proxy:
                print('Using Proxy',proxy)
                return get_html(url)
            else:
                print('Get Proxy Failed')
                return None
    except ConnectionError as e:
        #如果失败的，更换代理，重新调用自己
        print('Error Occurred',e.args)#打印错误信息
        proxy = get_proxy()
        count += 1
        return get_html(url,count)



def get_index(keyword,page):
    # data = {
    #     'query': keyword,
    #     'type' : 2,#代表请求文章，搜公众号为1
    #     'page' : page
    # }
    #queries = urlencode(data)
    query = 'oq=&query=%E9%A3%8E%E6%99%AF&_sug_type_=1&sut=0&lkt=0%2C0%2C0&s_from=input&ri=2&_sug_=n&type=2&sst0=1562897509064&page={page}&ie=utf8&p=40040108&dp=1&w=01015002&dr=1'.format(page=page)
    url = base_url.format(query=query)
    html = get_html(url)
    # print(html)
    return html

def parse_index(html):
    doc = pq(html)
    items = doc('.news-box .news-list li .txt-box h3 a').items()
    for item in items:
        yield item.attr('data-share')#这里直接打印html输出的data-share带有'&amp;'改成'&'就可以继续爬虫了，但是直接yield出来的data-share只有'&'，可以直接爬取



def get_detail(url):
    #微信文章没有反爬虫限制
    try:
        response = requests.get(url)
        print(response.status_code)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None

#解析源代码
def parse_detail(html):
    try:
        # print('html:',html)
        doc = pq(html)
        # print('doc:',doc)
        title = doc('.rich_media_title').text()
        # print(doc('.rich_media_title'))
        content = doc('.rich_media_content').text()
        #下面这个date的时间，死活提不出来，不知道为什么，把网页直接拿过来提，也没有成功
        if doc('.rich_media_meta_list #publish_time'):
            print(doc('.rich_media_meta_list #publish_time'))
        else:
            print('no date')
        date = doc('#publish_time').text()
        nickname = doc('#js_profile_qrcode > div > strong').text()
        wechat = doc('#js_profile_qrcode > div > p:nth-child(3) > span').text()
        return {
            'title':title,
            'content':content,
            'date':date,
            'nickname':nickname,
            'wechat':wechat
        }
    except XMLSyntaxError:#pyquery的解析错误
        return None

def save_to_mongo(data):
    if db['articles'].update({'content':data['content']},{'$set':data},True):#3个参数，update去重，根据标题是否唯一去重，
        print('Save to Mongo ',data['title'])
    else:
        print('Save to Mongo Failed',data['title'])

def main():
    for page in range(1,101):
        html = get_index(KEYWORD,page)
        # print('html:',html)
        if html:
            article_urls = parse_index(html)
            for article_url in article_urls:
                print('article_url:',article_url)
                article_html = get_detail(article_url)
                # print('article_html:',article_html)
                if article_html:
                      article_data = parse_detail(article_html)
                      print('article_data:',article_data)
                      article_data['url'] = article_url
                      if article_data:
                            save_to_mongo(article_data)

if __name__ == '__main__':
    # html = get_index('风景',1)
    # if html:
    #     article_urls = parse_index(html)
    main()
