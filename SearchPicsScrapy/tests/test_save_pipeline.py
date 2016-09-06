from ..SearchPicsScrapy.pipelines.SavePipeline import DBWriterPipeline, TasksItem, ResultsItem, run
from ..SearchPicsScrapy.spiders.google_spider import GoogleSpider

from mock import patch, sentinel, Mock
import pytest


@pytest.fixture
def fixt_keyword():
    return 'kitten'

@pytest.fixture
def fixt_item():
    return {'pic_link':'pic_img'}

@pytest.fixture
def fixt_broken_item():
    return {'error':True}

@pytest.fixture
def fixt_spider():
    return GoogleSpider()

@pytest.fixture
def fixt_task():
    return TasksItem.django_model.objects.get(keyword=fixt_keyword(), user=fixt_user())

@pytest.fixture
def fixt_user():
    return None

@pytest.fixture
def fixt_pipeline():
    return DBWriterPipeline()


ResultsItem.django_model.objects.all().delete()
TasksItem.django_model.objects.all().delete()
task = TasksItem.django_model.objects.create(keyword=fixt_keyword(), user=fixt_user(),
                                             status="IN_PROGRESS google")


def test_get_task(fixt_pipeline, fixt_keyword, fixt_user, fixt_task):

    with patch.object(fixt_pipeline, 'get_task', return_value=fixt_task) as mock_get_task:
        assert fixt_pipeline.get_task() == mock_get_task()

def test_save_result(fixt_pipeline, fixt_item, fixt_spider, fixt_task):
    fixt_pipeline.save_result(fixt_item, fixt_spider, fixt_task)
    result = ResultsItem.django_model.objects.get(task=fixt_task, link=fixt_item.keys()[0], img=fixt_item.values()[0])
    assert result != None

def test_search_finished(fixt_pipeline, fixt_spider, fixt_item, fixt_broken_item):
    fixt_pipeline.items_processed[fixt_spider.name] = 10
    assert fixt_pipeline.search_finished(fixt_spider, fixt_item) == True
    fixt_pipeline.items_processed[fixt_spider.name] = 9
    assert fixt_pipeline.search_finished(fixt_spider, fixt_item) == False
    assert fixt_pipeline.search_finished(fixt_spider, fixt_broken_item) == True


def test_process_item(fixt_pipeline, fixt_spider, fixt_item, fixt_keyword, fixt_task):
    fixt_spider.search_phrase.append(fixt_keyword)
    fixt_pipeline.items_processed[fixt_spider.name] = 9
    with patch.object(fixt_pipeline, "get_task", return_value=fixt_task) as mock_get_task, \
        patch.object(fixt_pipeline, "save_result") as mock_save_result:
        assert fixt_pipeline.process_item(fixt_item, fixt_spider) == fixt_item
        assert mock_get_task.call_count == 1
        assert mock_save_result.call_count == 1
    assert fixt_pipeline.items_processed[fixt_spider.name] == 0
