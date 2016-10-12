from __future__ import absolute_import
import datetime
import boto
import urllib
import zipfile
from boto.s3.key import Key
from django.conf import settings

print("TASKS")

from celery import shared_task
from main.models import *


import os
import sys
# sys.path.append('/home/user/Projects/FinalProject/SearchPicsDjango/SearchPicsDjango.')
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# # os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")



@shared_task
def add(x, y):
    print(x + y)

@shared_task
def upload_photo(url, username):
    print("upload")
    conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    bucket = conn.get_bucket(bucket_name)
    k = Key(bucket)
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent',
                         'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
    urllib.request.install_opener(opener)

    folder = '{}/'.format(str(username))
    print(folder)
    if 'http' not in url:
        url = 'http:'+url
    print(url)
    file = urllib.request.urlretrieve(url, settings.PIC_DIR + (url.replace('/','')))

    k.key = folder + url.replace('/','')
    k.set_contents_from_filename(file[0])
    print("posted")
    os.remove(file[0])
    print("removed")


# @shared_task
# def download_photos(user):
#     print("downloading")
#     conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
#     bucket_name = settings.AWS_STORAGE_BUCKET_NAME
#     bucket = conn.get_bucket(bucket_name)
#     path = ""
#     for key in bucket.list():
#         print(key)
#         if user == key.name.split("/")[0] and key.name.split("/")[1]!="":
#              path = settings.PIC_DIR + user + "/"
#              os.makedirs(path, exist_ok=True)
#              key.get_contents_to_filename( path + (key.name.split("/")[1]))
#   #  to_zip (path, user)
#
#
# def to_zip(src, dst):
#     zf = zipfile.ZipFile(settings.PIC_DIR+ dst+'.zip', 'w', zipfile.ZIP_DEFLATED)
#     abs_src = os.path.abspath(src)
#     for dirname, subdirs, files in os.walk(src):
#         for filename in files:
#             absname = os.path.abspath(os.path.join(dirname, filename))
#             arcname = absname[len(abs_src) + 1:]
#             print('zipping %s as %s' % (os.path.join(dirname, filename),
#                                   arcname))
#             zf.write(absname, arcname)
#     zf.close()

@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)


@shared_task
def del_old_queries():
    print("Deleting...")
    now = datetime.datetime.now()
   # six_hours = datetime.timedelta(hours=6)
    tasks = Tasks.objects.filter(date__lt=now)

    if len(tasks) > 0:
        Results.objects.filter(task_id__in=tasks).delete()
        print("OK...")
        tasks.delete()
    else:
        print("Nothing to delete")
