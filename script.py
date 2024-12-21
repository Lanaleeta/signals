import pandas as pd
import numpy as np
import datetime as dt
import pytz
import time 
import pandas_ta as ta
import requests
import calendar
import warnings
import os

from urllib.parse import urlencode
from urllib.request import urlopen
from datetime import datetime
from io import StringIO
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

warnings.filterwarnings('ignore')
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram(text: str):
  response = requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage', data={
    'chat_id': TELEGRAM_CHAT_ID,
    'text': text
  })
  if response.status_code != 200:
    raise Exception('sending error')

def add_indicators(data):
  data['sma_10'] = ta.sma(data['close'], length=10, append=True, adjust=True)
  data.columns = data.columns.str.lower()
  return data

def add_signals(data):
  data['sma_cross'] = ''
  moscow_tz = pytz.timezone('Europe/Moscow')
  f = lambda x: dt.datetime.fromtimestamp(int(x)/1000, moscow_tz).strftime('%Y-%m-%d %H:%M:%S')
  data.index = data.starttime.apply(f)
  for i in range((len(data) - 1), len(data)):
    #сигналы по SMA
    c, d, e, f = data['sma_10'][i - 1], data['sma_10'][i], data['close'][i - 1], data['close'][i]
    if f > d and e <= c:
      data['sma_cross'][i] = 'buy'
    elif f < d and e >= c:
      data['sma_cross'][i] = 'sell'
  return data

symbol = 'STMXUSDT'
tick_interval = '5'

# 60_000 - 200 5-минуток
start = str(calendar.timegm(datetime.utcnow().utctimetuple()) - 60_000)

url = 'https://api.bybit.com/v5/market/kline?symbol=' + symbol + '&interval=' + tick_interval + '&from=' + start

response = requests.get(url).json()
D = pd.DataFrame(response['result']['list'])
df = D

df = df.rename(columns = {0:'starttime', 1:'open', 2:'high', 3:'low', 4:'close', 5:'volume', 6:'turnover'})
df = pd.DataFrame(df, dtype=float)

itog = add_signals(add_indicators(df))

n_rows = itog[-1:]
if itog['sma_cross'].iloc[-1] == 'buy':
  print('Сигнал на покупку')
elif itog['sma_cross'].iloc[-1] == 'sell':
  print('Сигнал на продажу')
else:
  print('Сигнала нет')
