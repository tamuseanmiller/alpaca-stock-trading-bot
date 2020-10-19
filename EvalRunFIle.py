import os
os.environ['TF_MIN_GPU_MULTIPROCESSOR_COUNT'] = '2'
os.environ['APCA_API_BASE_URL'] = 'https://paper-api.alpaca.markets'
os.environ['APCA_API_KEY_ID'] = 'PKVQCPLCNIT0LP3PCG01'
os.environ['APCA_API_SECRET_KEY'] = '24F86p4D6CjNw0YEL4ZtcoiTpeSepcJxXccfsZH5'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:/Users/Mohit/PycharmProjects/SuperAIPR/newslstmstockbot/keys.json'
from bs4 import BeautifulSoup
import requests
import os
import time

def findGainingStocks():
    url = 'https://finance.yahoo.com/gainers'
    resp = requests.get(url)
    html = resp.content
    soup = BeautifulSoup(html, 'html.parser')
    tr_tags = soup.find_all('tr')
    td_tags = [tag.find('td') for tag in tr_tags]
    refresh = soup.find_all('meta', attrs={'http-equiv': 'refresh'})
    print(refresh)
    symbols = [tag.find('a').text for tag in td_tags if
               tag != None and '=' not in tag.find('a').text and '^' not in tag.find('a').text]
    # for s in symbols:
    # print('kool')
    global newsymbols
    newsymbols = symbols[0]
    return newsymbols

print('eval wth "Flair Custom Module", or eval with "Natural Language Understanding by Google"? Answer 1 or 2')
var = int(input())
print('With AI an recomended stock, or your own stock? Answer 1 or 2')
varvar = int(input())
if varvar == 2:
    print('What stock would you like to use?, (TYPE ONLY STOCK NAME, NO SPACES!)')
    varvarvar = str(input())
if var == 1:
    if varvar == 1:
        findGainingStocks()
        print('Trading stock', newsymbols)
        time.sleep(5)
        os.system(
            'python eval.py test --window-size=10 --model-name=model_AMD_alpha --run-bot=y --stock-name=' + newsymbols + ' --debug')
    if varvar == 2:
        os.system(
            'python eval.py test --window-size=10 --model-name=model_AMD_alpha --run-bot=y --stock-name=' + varvarvar + ' --debug')
if var == 2:
    if varvar == 1:
        findGainingStocks()
        print('Trading stock', newsymbols)
        time.sleep(5)
        os.system(
            'python eval.py test --window-size=10 --model-name=model_AMD_alpha --run-bot=y --stock-name=' + newsymbols + ' --natural-lang --debug')
    if varvar == 2:
        os.system(
            'python eval.py test --window-size=10 --model-name=model_AMD_alpha --run-bot=y --stock-name=' + varvarvar + ' --natural-lang --debug')
