from datetime import timedelta,datetime
import time
from curl_cffi import requests
import threading
from functools import *
from loguru import logger
def ckeck_one_day(func):
    def pass_func(name,func_name):
        logger.info(f'{name}-距离上次执行-{func.__name__}-还没有一天')
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(args,kwargs)
        key=func.__name__+'_ts'
        this=args[0]
        this.print()
        ts=kwargs['wallet'].get(key)
        if not ts:
            return func(*args, **kwargs)
        name=kwargs['wallet']['name']
        dt1 = datetime.fromtimestamp(ts)
        now = datetime.fromtimestamp(time.time())
        # 计算时间差
        time_difference = abs(now-dt1)
        if time_difference == timedelta(days=1):
            return func(*args, **kwargs)
        else:
            return pass_func(name,func.__name__)
    return wrapper
def log_args(func):
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        key=func.__name__+'_ts'
        ts=kwargs['wallet'][key]
        print(f"{ts}")
        func(*args, **kwargs)
        return 
    return wrapper
class test:
    def print(self):
        print('ok')
    @ckeck_one_day
    def checkin(self,wallet={'checkin_ts':time.time()}):
        print(wallet)
a=test()
a.checkin(wallet={'checkin_ts':time.time(),'name':'test'})


