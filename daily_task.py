from main import Plume_TestNet_Bot,logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import time
from apscheduler.triggers.cron import CronTrigger
bot=Plume_TestNet_Bot(show_point=True)


# 创建调度器
scheduler = BackgroundScheduler()

# 定义一个每24小时执行一次的触发器
trigger = IntervalTrigger(hours=24)

# 添加任务到调度器
scheduler.add_job(bot.do_daily_tasks, trigger)
bot.do_daily_tasks()
# 启动调度器
scheduler.start()

# 让主线程保持运行，以便调度器可以执行任务
try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    # 关闭调度器
    scheduler.shutdown()
