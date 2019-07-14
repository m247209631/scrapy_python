#由于gallery变量不在html里面，所以不能用beautifulsoup和PyQuery来解析，用正则来解析
import requests
from urllib.parse import urlencode
from requests.exceptions import RequestException
import json,re,demjson
from bs4 import BeautifulSoup
from selenium import webdriver
from config import *
import pymongo
import os
from hashlib import md5
from multiprocessing import Pool

client = pymongo.MongoClient(MONGO_URL)#如果有警告可以在()内加入connect=False
db = client[MONGO_DB]

def get_page_index(offset,keyword):
    data = {
        # 'aid': 24,#注意把这个注释掉，否则无法爬取数据
        'app_name': 'web_search',
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': 20,
        'en_qc': 1,
        'cur_tab': 1,
        'from': 'search_tab',
        'pd': 'synthesis',
        'timestamp': 1559960492625
    }
    url = 'https://www.toutiao.com/api/search/content/?'+urlencode(data)#urlencode()将字典对象转换成url的请求参数
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求索引出错1')
        return None
def parse_page_index(html):
    data = json.loads(html)
    # print(data)
    if data and 'data' in data.keys():  # data存在和'data'在data.keys中
        if  data.get('data') == None:
            # print('No data')
            return
        else:
            for item in data.get('data'):
                yield item.get('article_url')

def get_page_detail(url):
    headers = {
       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'
    }
    try:
        response = requests.get(url,headers=headers)#这里必须使用headers否则response.text为空
        # response = requests.get(url)
        if response.status_code == 200:
            # print(response.text)
            return response.text
        return None
    except RequestException:
        # print('请求索引出错2',url)
        return None
def parse_page_detail(html,url):
    soup = BeautifulSoup(html,'lxml')
    if len(soup.select('title')) != 0:
        title = soup.select('title')[0].get_text()
        # print(title)
    images_pattern = re.compile('articleInfo: ({.*?}),\s+?commentInfo',re.S)
    result = re.search(images_pattern,html)
    #print(result)
    if result:
        # print(result.group(1))
        # print(type(result.group(1)))
        data=demjson.decode(result.group(1))#这里使用了demjson.decode()，是因为输出的结果没有双引号，直接字符开头
        # print(data)
        # data_json = json.loads(str(data).replace("'",'"'))
        # if data and 'sub_images' in data.keys():
        #     print(1222)
        # else:
        #     print(2111)
        if data and 'content' in data.keys():
            # print(data.get('content'))
            image_url_pattern = re.compile('&quot;(http://.*?)&quot')#由于content对应的value，不是字典，是str，用正则抓取图片的url
            images_url = re.findall(image_url_pattern,data.get('content'))#findall抓取全部的url，输出为list
            # print(image_url)
            for url in images_url:
                download_image(url)
            return {
                "url":url,
                "title":title,
                "images_url":images_url,
            }
        #     sub_images = data.get('sub_images')
        #     images = [item.get('url') for item in sub_images]
        #     return {
        #         'title':title,
        #         'url':url,
        #         'images':images
        #     }
def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('存储到MongoDB成功',result)
        return True
    return False
def download_image(url):#下载图片
    print('正在下载',url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            save_image(response.content) #response.content是指文件的二进制内容，一般保存图片用这个，response.text返回网页
        return None
    except RequestException:
        # print('请求索引出错1')
        return None
def save_image(content):
    #os.getcwd()返回当前工作目录，md5.digest()与md5.hexdigest()分别返回二进制和十六进制的哈希值
    #md5()中()内的对象需要是bytes对象
    file_path ='{0}/{1}.{2}'.format(os.getcwd(),md5(content).hexdigest(),'jpg')
    if not os.path.exists(file_path):
        with open(file_path,'wb') as f:
            f.write(content)
            f.close() #我猜这里没有应该也可以吧

def main(offset):
    html = get_page_index(offset,KEYWORD)
    # print(html)
    for url in parse_page_index(html):
        # print(url)
        html = get_page_detail(url)
        #print(html)
        if html:
            result=parse_page_detail(html,url)
            # print(result)
            if result:
                save_to_mongo(result)

if __name__ == '__main__':
    # main()
    groups = [x*20 for x in range(GROUP_START,GROUP_END+1)]
    pool =Pool()
    pool.map(main,groups)


