# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from google.cloud import language_v1
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
import requests


def runNewsAnalysis(stock, api):
    url = 'https://www.tradingview.com/screener/'

    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    import time
    from bs4 import BeautifulSoup

    # Starts Chrome in headless mode using selenium
    # WINDOW_SIZE = "1920,1080"
    # chrome_options = Options()
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
    # chrome_options.binary_location = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    # service = Service('C:/Users/Sean/AppData/Local/Temp/Rar$EXa34860.36409/chromedriver.exe')
    # service.start()
    # driver = webdriver.Chrome(executable_path='C:/Users/Sean/AppData/Local/Temp/Rar$EXa34860.36409/chromedriver.exe',
    #                           chrome_options=chrome_options)
    # driver.get(url)
    # html = driver.find_element_by_css_selector('table')
    #
    # # Uses BeautifulSoup to parse table
    # soup = BeautifulSoup(driver.page_source, 'lxml')
    #
    # job_elems = soup.find_all('tbody', attrs={"class": "tv-data-table__tbody"})
    #
    # rows = job_elems[1].findAll('td')
    #
    # for row in rows:
    #     row = row.find('a')
    #     # print(row.findAll("tv-screener-table__signal tv-screener-table__signal--strong-buy"))
    #     # ans = row.findAll('a')
    #     if row is not None:
    #         print(row)

    # print(job_elems[1].findAll('td'))

    # driver.quit()

    # Instantiates a client
    # [START language_python_migration_client]
    client = language.LanguageServiceClient()
    # [END language_python_migration_client]

    # NewsAPI API call
    url = ('https://newsapi.org/v2/everything?'
           'apiKey=d42e88f1fb624084891e89df549c06ff&'
           'q=' + stock + '&'
                          'sources=reuters, the-wall-street-journal, cnbc&'
                          'language=en&'
                          'sortBy=publishedAt&'
                          'pageSize=100')
    response = requests.get(url).json()['articles']

    # Polygon News API call
    news = api.polygon.news(stock)

    file = open('news.txt', 'w')

    sentiment = 0
    for line in response:
        words = str(line['content'])
        file.write(words)

        document = {
            "content": words,
            "type": enums.Document.Type.PLAIN_TEXT}

        # Detects the sentiment of the text
        sentiment += client.analyze_sentiment(document=document,
                                              encoding_type=enums.EncodingType.UTF8).document_sentiment.magnitude

    for source in news:
        words = source.summary
        document = {
            "content": words,
            "type": enums.Document.Type.PLAIN_TEXT}

        # Detects the sentiment of the text
        sentiment += client.analyze_sentiment(document=document,
                                              encoding_type=enums.EncodingType.UTF8).document_sentiment.magnitude

    return sentiment
