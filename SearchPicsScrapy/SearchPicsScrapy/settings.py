# -*- coding: utf-8 -*-

# Scrapy settings for SearchPicsScrapy project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'SearchPicsScrapy'

SPIDER_MODULES = ['SearchPicsScrapy.SearchPicsScrapy.spiders']
NEWSPIDER_MODULE = 'SearchPicsScrapy.SearchPicsScrapy.spiders'

ROBOTSTXT_OBEY = False
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

DOWNLOAD_DELAY = 1

ITEM_PIPELINES = {
    'SearchPicsScrapy.SearchPicsScrapy.pipelines.SavePipeline.DBWriterPipeline': 300,
}

