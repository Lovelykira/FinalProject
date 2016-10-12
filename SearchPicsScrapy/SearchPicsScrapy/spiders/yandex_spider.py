from scrapy_redis.spiders import RedisSpider

import logging
import json


class YandexSpider(RedisSpider):
    """
    Class YandexSpider searches the results in instagram.ua
    """
    name = "yandex"
    allowed_domains = ["yandex.ua"]

    def __init__(self, search=""):
        super(YandexSpider, self).__init__()
        self.search_phrase = []
        self.num_items = 3
        self.user_pk = []

    def parse(self, response):
        """
        The method that parses the response page.

        @param response:
        @return: if everything is ok, it returns dict with picture's image link as key and pictures image source as value.
        if not it returns dict with 'error' as key.
        """
        #inspect_response(response, self)
        try:
            images_list = response.xpath(".//div[@class='page-layout__column page-layout__column_type_content']")[0]
            images_list = images_list.xpath(".//div[@class='page-layout__content-wrapper b-page__content']")[0]
            images_list = images_list.xpath(".//div[@class='serp-controller__content']")[0]
            links = images_list.xpath(".//a[@class='serp-item__link']")[:self.num_items]
            for link in links:
                img = link.xpath("./img")
                pic_link = 0
                pic_img = 0
                try:
                    link = link.extract()
                    pic_link = link.split('href="')[1]
                    pic_link = pic_link.split('">')[0]
                    pic_link = 'https://yandex.ua'+pic_link
                except:
                   logging.log(logging.ERROR, "Spider {} couldn't parse the pic's link".format(self.name))
                try:
                    img = img.extract()[0]
                    pic_img = img.split('src="')[1]
                    pic_img = pic_img.split('" onerror=')[0]
                except:
                    logging.log(logging.ERROR, "Spider {} couldn't parse the pic's img".format(self.name))
                logging.log(logging.INFO, "Spider {} proceeded {}".format(self.name, {str(pic_link): str(pic_img)}))
                yield {str(pic_link): str(pic_img)}
        except:
            logging.log(logging.ERROR, "Spider {} couldn't parse the page".format(self.name))
            yield {'error': True}

    def make_request_from_data(self, data):
        """
        The method that analyzes data from redis list.

        It splits the data into search phrase and user pk and stores this variables in spider's fields.
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

        return self.make_requests_from_url('https://yandex.ua/images/search?text=' + data)
