import random
from scrapy.conf import settings
from scrapy import log
from fake_useragent import UserAgent


class RandomUserAgentMiddleware:

    def process_request(self, request, spider):
        ua = UserAgent()
        agent = ua.random
        if agent:
            request.headers.setdefault('User-Agent', agent)
            #this is just to check which user agent is being used for request
            spider.log(
                u'User-Agent: {} {}'.format(request.headers.get('User-Agent'), request),
                level=log.DEBUG
            )
