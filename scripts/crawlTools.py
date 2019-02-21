# crawl tools
# -*- coding: utf-8 -*

import requests
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from namedEntityTools import *

def retrieveAIDailyAuto(cardNum = 10):
    titles = []
    contents = []

    driver = webdriver.Chrome()
    url = 'https://www.jiqizhixin.com/dailies'
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    SCROLL_PAUSE_TIME = 5
    scrollNum = cardNum // 10 + 1

    element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'daily-every__item')))
    for k in range(scrollNum):
        cards = driver.find_elements_by_class_name("daily-every__item")
        for card in cards[k*10: k*10+10]:
            card.find_element_by_class_name("daily-every__title").send_keys('\n')
            wait = WebDriverWait(driver, 5)
            element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'daily-show')))
            window = driver.find_element_by_class_name("daily-show")
            title = window.find_element_by_class_name("daily__title").text
            content = window.find_element_by_class_name("daily__content").text
            titles.append(re.sub(r'^\s*$', '。', title).encode('utf-8'))
            contents.append(re.sub(r'^\s*$', '。', content).encode('utf-8'))
            driver.find_element_by_class_name("daily__close").click()
            wait = WebDriverWait(driver, 5)
            element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'daily-every__item')))
        time.sleep(SCROLL_PAUSE_TIME)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        time.sleep(SCROLL_PAUSE_TIME)
        
    driver.close()
    return titles[:cardNum], contents[:cardNum], []


def retrieveAIDailyURL(url):
    titles = []
    contents = []

    driver = webdriver.Chrome()
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'daily-show')))
    window = driver.find_element_by_class_name("daily-show")
    title = window.find_element_by_class_name("daily__title").text
    content = window.find_element_by_class_name("daily__content").text
    titles.append(re.sub(r'^\s*$', '。', title).encode('utf-8'))
    contents.append(re.sub(r'^\s*$', '。', content).encode('utf-8'))
    driver.find_element_by_class_name("daily__close").click()
    wait = WebDriverWait(driver, 5)
    element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'daily-every__item')))
        
    driver.close()
    return titles, contents, []


def retrieveArticle(url):
    cookie=None
    sess = requests.session
    header = {'cookie':cookie}
    res = requests.get(url,headers=header)
    soup = BeautifulSoup(res.text,'html.parser')

    title = soup.title.string
    body = soup.body

    description = ''
    if body.find('blockquote'):
        for para in body.find('blockquote').find_all('p'):
            description += para.text
        body.find('blockquote').decompose()

    content = ''
    for para in body.find_all('p'):
        content += para.text
        
    bodyText = body.text
    
    titleDeleteEmptyLine = re.sub(r'^\s*$', '。', title)
    contentDeleteEmptyLine = re.sub(r'^\s*$', '。', content)
    descriptionDeleteEmptyLine = re.sub(r'^\s*$', '。', description)
    bodyTextDeleteEmptyLine = re.sub(r'^\s*$', '。', bodyText)

    content = ''
    for para in body.find_all('p'):
        content += para.text
    contentTextDeleteEmptyLine = re.sub(r'^\s*$', '。', content)

    listItems = []
    if body.find_all('tbody'):
        for table in body.find_all('tbody'):
            for td in table.find_all('td'):
                listItems.append(td.text.encode('utf-8').strip())
    if body.find_all('li'):
        for li in body.find_all('li'):
            listItems.append(str(li.text.encode('utf-8')).strip())
    if body.find_all('h4'):
        for h4 in body.find_all('h4'):
            listItems.append(str(h4.text.encode('utf-8')).strip())
    if body.find_all('h3'):
        for h3 in body.find_all('h3'):
            listItems.append(str(h3.text.encode('utf-8')).strip())
    if body.find_all('h5'):
        for h5 in body.find_all('h5'):
            listItems.append(str(h5.text.encode('utf-8')).strip())

    if not containKeyWords(title, ['精选','推荐','列表','篇','排名','总结','集合','合集','最佳']):
        return [str(titleDeleteEmptyLine.encode('utf-8'))], [str(contentDeleteEmptyLine.encode('utf-8'))], [listItems]

    for item in listItems:
        bodyTextDeleteEmptyLine = re.sub(item, '', bodyTextDeleteEmptyLine)

    return [str(titleDeleteEmptyLine.encode('utf-8'))], [str(contentTextDeleteEmptyLine.encode('utf-8'))], [listItems]


def crawlArticle(articleType, articleUrl='', autoCrawlAI=False, articleNumberAI=10):
    '''
    input:  articleType: string, 'AIDaily' or other, case insensitive;
            articleUrl: string, default to '';
            autoCrawlAI: boolean, only work when articleType='AI Daily', default to True;
            articleNumberAI: int, only work when articleType='AI Daily' and autoCrawlAI=True, default to 10;
    
    output: list of title;
            list of content;
            list of description (only has element for articles with short description)
    '''
    if articleType.lower().strip() == 'aidaily':
        if articleUrl:
            return retrieveAIDailyURL(articleUrl)
        else:
            if not autoCrawlAI:
                return 'Invalid inputs, try again!'
            return retrieveAIDailyAuto(articleNumberAI)
    else:
        if not articleUrl:
            return 'Invalid articleUrl, try again!'
        return retrieveArticle(articleUrl)
