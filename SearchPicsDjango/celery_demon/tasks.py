from __future__ import absolute_import
import os
import datetime
import boto
import urllib
from boto.s3.key import Key
from django.conf import settings

from celery import shared_task
from main.models import *


@shared_task
def upload_photo_to_aws(url, username, keyword):
    conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    bucket = conn.get_bucket(bucket_name)
    k = Key(bucket)
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent',
                         'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
    urllib.request.install_opener(opener)

    folder = '{}/{}/'.format(str(username), keyword)
    if 'http' not in url:
        url = 'http:'+url
    file = urllib.request.urlretrieve(url, settings.PIC_DIR + (url.replace('/','')))

    k.key = folder + url.replace('/','')
    k.set_contents_from_filename(file[0])
    os.remove(file[0])


@shared_task
def del_old_queries():
    print("Deleting...")
    now = datetime.datetime.now()
    tasks = Tasks.objects.filter(date__lt=now)
    if len(tasks) > 0:
        Results.objects.filter(task_id__in=tasks).delete()
        print("OK...")
        tasks.delete()
    else:
        print("Nothing to delete")
