from ..SearchPicsScrapy.spiders.google_spider import GoogleSpider

from mock import patch, sentinel, Mock
import pytest
import json

@pytest.fixture
def fixt_spider():
    return GoogleSpider()

@pytest.fixture
def fixt_data():
    return {'value':'kitten', 'user': 'None'}

@pytest.fixture
def fixt_error_data():
    return {'error': True}

def test_make_request_from_data(fixt_spider, fixt_data):
    with patch.object(fixt_spider, 'make_requests_from_url') as mock_make_requests_from_url:
        fixt_spider.make_request_from_data(json.dumps(fixt_data))
        mock_make_requests_from_url.assert_called_once()
    assert fixt_spider.search_phrase[0] == fixt_data['value']

def test_parse(fixt_spider, fixt_data, fixt_error_data, response="some text"):
    fixt_spider.search_phrase = fixt_data['value']
    for return_val in fixt_spider.parse(response):
        assert return_val == fixt_error_data
