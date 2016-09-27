from scrapy_djangoitem import DjangoItem

import json
import logging
import sys
import os
import redis
up = lambda x: os.path.dirname(x)
sys.path.insert(0, os.path.join(up(up(up(up(os.path.abspath(__file__))))), 'SearchPicsDjango'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SearchPicsDjango.settings")
import django
django.setup()

from main.models import Tasks, Results

FINISHED = "FINISHED"


class TasksItem(DjangoItem):
    django_model = Tasks


class ResultsItem(DjangoItem):
    django_model = Results


class DBWriterPipeline(object):
    """
    Class that processes items, returned by spiders and writes data to database.
    """
    def __init__(self):
        self.items_processed={'google':0,'yandex':0,'instagram':0}

    def get_task(self, keyword, user_id, spider_name):
        """
        The method that returns Task object for current user and search phrase.

        @param keyword: str.
        @param user_id: current user id or None for anonymous user.
        @return: Task object.
        """
        if user_id != -1:
            task = TasksItem.django_model.objects.get(keyword=keyword, user_id=user_id, site=spider_name)
        else:
            task = TasksItem.django_model.objects.get(keyword=keyword, user=None, site=spider_name)
        return task

    def save_result(self, item, spider, task):
        """
        The method that saves the result of the search to database.

        @param item: item, returned by spider's parse() method.
        @param spider: Spider object.
        @param task: current Task object.
        """
        for link, img in item.items():
            result = ResultsItem()
            result['task'] = task
            result['link'] = link
            result['img'] = img
            result['rank'] = self.items_processed[spider.name]
            result.save()

    def search_finished(self, spider, item):
        """
        The method that checks if the search is over.
        It is over when the pipeline processed a number of items equal to spider.num_items or if error occurred
        during parse.
        @param spider: Spider object.
        @param item: current Task item.
        @return: True if the search is finished; False - otherwise.
        """
        return self.items_processed[spider.name] == spider.num_items or 'error' in item.keys()

    def process_item(self, item, spider):
        """
        The method that processes the item.

        If no error occurred it saves the result of spider's search.
        Then if the spider finished searching the method updates table 'tasks' setting 'status' to 'FINISHED' and sends
        the signal to webserver about it by publishing json that contains the search phrase and user_id to redis channel.
        @param item: dict with picture's image link as key and pictures image source as value.
        @param spider: Spider object
        @return: item
        """
        search_phrase = spider.search_phrase[0]
        self.items_processed[spider.name] += 1
        logging.log(logging.INFO, "Pipeline processing {} of {}. Item #{}".format(search_phrase, spider.search_phrase,
                                                                                self.items_processed))

        item = dict(item)
        task = self.get_task(search_phrase, spider.user_pk, spider.name)

        if not 'error'in item.keys():
            self.save_result(item, spider, task)

        if self.search_finished(spider, item):
            run(search_phrase, task.user)
            spider.search_phrase = spider.search_phrase[1:]

            self.items_processed[spider.name] = 0
            cur_status = FINISHED
            TasksItem.django_model.objects.filter(pk=task.pk).update(status=cur_status)
            logging.log(logging.DEBUG, "Pipeline processing {}. FINISHED".format(search_phrase))
        return item


def run(search_phrase, user):
    """
    The function that publishes json that contains the search phrase and user_id to redis channel.

    @param search_phrase: str
    """
    if user:
        user_id = user.id
    else:
        user_id = -1
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    message =  json.dumps({'search_phrase':search_phrase, 'user_id':user_id})
    r.publish('our-channel',message)
    logging.log(logging.INFO, "Pipeline sent message({}) to webserver".format(message))