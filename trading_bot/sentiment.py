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
import coloredlogs
import logging
import flair
from flair.models import TextClassifier
from flair.data import Sentence
import re
from flair.embeddings import ELMoEmbeddings


def clean(raw):
    """ Remove hyperlinks and markup """
    result = re.sub("<[a][^>]*>(.+?)</[a]>", 'Link.', raw)
    result = re.sub('&gt;', "", result)
    result = re.sub('&#x27;', "'", result)
    result = re.sub('&quot;', '"', result)
    result = re.sub('&#x2F;', ' ', result)
    result = re.sub('<p>', ' ', result)
    result = re.sub('</i>', '', result)
    result = re.sub('&#62;', '', result)
    result = re.sub('<i>', ' ', result)
    result = re.sub("\n", '', result)
    result = re.sub("&#39;", '\'', result)
    return result


# Not used right now
def decide_stock():
    coloredlogs.install(level="DEBUG")
    url = 'https://finance.yahoo.com/screener/predefined/day_gainers'

    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    import time
    from bs4 import BeautifulSoup

    # Starts Chrome in headless mode using selenium
    WINDOW_SIZE = "1920,1080"
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
    chrome_options.binary_location = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    service = Service('C:/Users/Sean/Documents/chromedriver.exe')
    service.start()
    driver = webdriver.Chrome(executable_path='C:/Users/Sean/Documents/chromedriver.exe',
                              chrome_options=chrome_options)
    driver.get(url)
    html = driver.find_element_by_css_selector('table')

    # Uses BeautifulSoup to parse table
    soup = BeautifulSoup(driver.page_source, 'lxml')

    job_elems = soup.findAll('tbody')

    rows = job_elems.findAll('td')

    for row in rows:
        row = row.findAll('ta')
        # print(row.findAll("tv-screener-table__signal tv-screener-table__signal--strong-buy"))
        # ans = row.findAll('a')
        if row is not None:
            print(row)

    print(job_elems.findAll('tr'))

    driver.quit()


def runNewsAnalysis(stock, api, natural_lang):
    logging.warning("Running sentiment with Natural Language set to: " + str(natural_lang))
    coloredlogs.install(level="DEBUG")
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

    flair_sentiment = flair.models.TextClassifier.load('en-sentiment')

    # NewsAPI API call
    url = ('https://newsapi.org/v2/everything?'
           'apiKey=d42e88f1fb624084891e89df549c06ff&'
           'qInTitle=\"' + stock + '\"&'
                                   'sources=reuters, the-wall-street-journal, cnbc&'
                                   'language=en&'
                                   'sortBy=publishedAt&'
                                   'pageSize=50')

    response = requests.get(url).json()['articles']

    # Polygon News API call
    news = api.polygon.news(stock)

    file = open('news.txt', 'w')

    sentiment = 0

    # Iterates through every news article from News API
    for line in response:
        words = str(line['content'])
        file.write(clean(words))

        if not natural_lang:

            # Runs Flair sentiment analysis
            sentence = Sentence(str(words))
            flair_sentiment.predict(sentence)
            total_sentiment = sentence.labels
            logging.info(str(words))

            # Checks to see if the sentiment is negative and subtracts by how negative flair thinks it is
            if total_sentiment[0].value == 'NEGATIVE':
                logging.warning(str(total_sentiment[0].value) + " : " + str(total_sentiment[0].to_dict()['confidence']))
                sentiment -= total_sentiment[0].to_dict()['confidence'] / 2  # Flair favors negative outcomes

            # Checks to see if the sentiment is positive and adds how positive flair thinks it is
            elif total_sentiment[0].value == 'POSITIVE':
                logging.debug(str(total_sentiment[0].value) + " : " + str(total_sentiment[0].to_dict()['confidence']))
                sentiment += total_sentiment[0].to_dict()['confidence']

        # Checks to see if you're using natural language
        else:

            document = {
                "content": words,
                "type": enums.Document.Type.PLAIN_TEXT}

            # Check for connection errors and retry 30 times
            cnt = 0
            while cnt <= 30:
                try:
                    # Detects the sentiment of the text
                    sentiment += client.analyze_sentiment(document=document,
                                                          encoding_type=enums.EncodingType.UTF8).document_sentiment.magnitude
                    break

                except:
                    logging.warning("Lost connection, retrying in 30s (" + str(cnt) + "/30)")
                    time.sleep(30)
                    cnt += 1
                    continue

    # Iterates through every news article on Polygon news
    for source in news:
        words = source.summary
        file.write(clean(words))
        file.write('\n')

        # Checks to see if you're using Flair
        if not natural_lang:

            # Runs Flair sentiment analysis
            sentence = Sentence(str(words))
            flair_sentiment.predict(sentence)
            total_sentiment = sentence.labels
            logging.info(str(words))

            # Checks to see if the sentiment is negative and subtracts by how negative flair thinks it is
            if total_sentiment[0].value == 'NEGATIVE':
                logging.warning(str(total_sentiment[0].value) + " : " + str(total_sentiment[0].to_dict()['confidence']))
                sentiment -= total_sentiment[0].to_dict()['confidence'] / 2  # Flair favors negative outcomes

            # Checks to see if the sentiment is positive and adds how positive flair thinks it is
            elif total_sentiment[0].value == 'POSITIVE':
                logging.debug(str(total_sentiment[0].value) + " : " + str(total_sentiment[0].to_dict()['confidence']))
                sentiment += total_sentiment[0].to_dict()['confidence']

        # Checks to see if you're using natural language
        else:

            document = {
                "content": words,
                "type": enums.Document.Type.PLAIN_TEXT}

            # Check for connection errors and retry 30 times
            cnt = 0
            while cnt <= 30:

                try:
                    # Detects the sentiment of the text
                    sentiment += client.analyze_sentiment(document=document,
                                                          encoding_type=enums.EncodingType.UTF8).document_sentiment.magnitude
                    break

                except:
                    logging.warning("Lost connection, retrying in 30s (" + str(cnt) + "/30)")
                    time.sleep(30)
                    cnt += 1
                    continue

    file.close()

    return sentiment
