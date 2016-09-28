from scrapy_redis.spiders import RedisSpider

import json
import logging


class InstagramSpider(RedisSpider):
    """
    Class InstagramSpider searches the results in instagram.com
    """
    name = "instagram"
    allowed_domains = ["instagram.com"]

    def __init__(self, search=""):
        super(InstagramSpider, self).__init__()
        self.search_phrase = []
        self.num_items = 10
        self.user_pk = []

    def parse(self, response):
        """
        The method that parses the response page.

        @param response:
        @return: if everything is ok, it returns dict with picture's image link as key and pictures image source as value.
        if not it returns dict with 'error' as key.
        """
        pic_link = 'https://www.instagram.com/explore/tags/' + self.search_phrase[0]
        try:
            data = response.xpath("body").xpath("p").extract()
            images_list = data[0].split('display_src": "')[1:self.num_items+1]
            for image in images_list:
                pic_img = image.split('"}')[0]
                pic_img = str(pic_img)
                logging.log(logging.INFO, "Spider {} proceeded {}".format(self.name, {str(pic_link): str(pic_img)}))
                yield {pic_link: pic_img}
        except:
            logging.log(logging.ERROR, "Spider {} couldn't parse the page".format(self.name))
            yield {'error': True}

    def make_request_from_data(self, data):
        """
        The method that analyzes data from redis list.

        It splits the data into search phrase and user pk and stores this variables in spider's fields.
        If data contains spaces, it would be replaced by _.
        @param data:
        @return: calls make_requests_from_url method.
        """
        data_json = json.loads(data)
        data = data_json['value']
        if data_json['user']:
            self.user_pk.append(data_json['user'])
        else:
            self.user_pk.append(-1)
        self.search_phrase.append(data)
        if " "  in data:
            data = data.replace(" ", "_")

        return self.make_requests_from_url('https://www.instagram.com/explore/tags/' + data + '/?__a=1')


