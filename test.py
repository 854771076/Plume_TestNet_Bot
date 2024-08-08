from datetime import timedelta,datetime
import time
from curl_cffi import requests
import threading
from geopy.distance import great_circle
from functools import *
from loguru import logger
from main import *
bot=Plume_TestNet_Bot(invited='RRU30',wallet_path='./wallets')
bot.do_daily_tasks()