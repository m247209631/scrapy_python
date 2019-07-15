from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pyquery import PyQuery as pq
from config import *
import pymongo
import re
import time

client =pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

# chrome_options = Options()
# chrome_options.add_argument('--headless')
# browser = webdriver.Chrome(chrome_options=chrome_options)#以上3行使用无界面浏览器设置
browser = webdriver.Chrome()
# browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)  #selenium已经放弃PhantomJS了，建议使用火狐或者谷歌无界面浏览器
wait = WebDriverWait(browser,60)

#browser.set_window_size(1400,900)  #使用phantomjs时设置窗口大小

def search():
    print('正在搜索')     #使用无界面浏览器时用
    try:
        browser.get('http://www.taobao.com')
        # #进行密码登录
        # element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#J_SiteNavLogin > div.site-nav-menu-hd > div.site-nav-sign > a.h')))
        # element.click()
        # time.sleep(10)
        # element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#J_QRCodeLogin > div.login-links > a.forget-pwd.J_Quick2Static')))
        # element.click()
        # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#J_Form > div.field.username-field > span.ph-label'))).send_keys("m247209631")
        # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#TPL_password_1'))).send_keys("MAXIN100822")
        # time.sleep(10)
        # # wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_SubmitStatic'))).click()

        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#q"))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button'))
        )
        input.send_keys(KEYWORD)
        submit.click()
        total = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total'))
        )
        get_products()
        # return total.text
        return total
    except TimeoutException:
        return search()

def next_page(page_number):
    print('正在翻页',page_number)   #使用无界面浏览器时用
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input"))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        input.clear()
        input.send_keys(page_number)
        submit.click()
        #EC.text_to_be_present_in_element,这个元素里面有这个文字
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number)))
        get_products()
    except TimeoutException:
        return next_page(page_number)

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MONGODB成功',result)
    except Exception:   #这里使用了父类的异常
        print('存储到MONGODB失败',result)

def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')))#其中的#代表id，.代表class，(By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')，需要加()，否则会报参数错误
    html = browser.page_source   #获取网页源代码
    doc = pq(html)   #解析源代码
    items = doc('#mainsrp-itemlist .items .item').items()  #调用所有items方法得到所有选择的内容
    for item in items:
        product = {
            'image': item.find('.pic img').attr('data-src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text(),
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location':item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)

def main():
    # search()
    try:
        total = search()
        for item in total:
            # total_number = int(re.compile('(\d+)').search(item.text).group(1))
            total_number = int(re.search('(\d+)',item.text).group(1))
            print(total_number)
        for i in range(2,total_number+1):
            next_page(i)
    except Exception:
        print('出错了')
    finally:
        # browser.close()
        pass
if  __name__ == '__main__':
    main()
