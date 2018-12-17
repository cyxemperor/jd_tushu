BOT_NAME = 'book'

SPIDER_MODULES = ['book.spiders']
NEWSPIDER_MODULE = 'book.spiders'

# LOG_LEVEL = "WARNING"

#指定了去重的类
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

#指定了调度器的类
SCHEDULER = "scrapy_redis.scheduler.Scheduler"

#调度器的内容是否持久化
SCHEDULER_PERSIST = True

#redis的url地址
REDIS_URL = "redis://127.0.0.1:6379"

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'

ROBOTSTXT_OBEY = False