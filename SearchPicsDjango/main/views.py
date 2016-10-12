from django.shortcuts import render
from django.views.generic import TemplateView, View, FormView
from django.http import HttpResponse,JsonResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from datetime import datetime, timedelta
import re
import json
import redis
import logging
import requests

from django.conf import settings
from io import StringIO, BytesIO
import zipfile
import glob
import os

from .models import Results, Tasks
from .forms import LoginForm, RegistrationForm

#from celery_demon.tasks import download_photos

SPIDERS = ['google', 'yandex', 'instagram']
START_STATUS = "IN_PROGRESS"
FINISHED = "FINISHED"

logger = logging.getLogger(__name__)


def byRank(item):
    return item.rank


def byID(item):
    return item.id


class SearchView(TemplateView):
    """
    Class SearchView.
    """
    template_name = "search.html"

    def get(self, request, *args, **kwargs):
        """
        GET method.

        Gets all results for current user by his search phrase and sorts them by rank.
        """
        if kwargs['id'] != "anonymous":
            tasks = Tasks.objects.filter(keyword=kwargs['phrase'], user_id=str(kwargs['id']))
        else:
            tasks = Tasks.objects.filter(keyword=kwargs['phrase'], user=None)
        pics = Results.objects.filter(task__in=tasks)
        pics = sorted(pics, key=byRank)
        return render(request, 'search.html', {'pics':pics})



class MainView(TemplateView):
    """
    Class MainView.
    """
    template_name = "index.html"

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(MainView, self).dispatch(request, *args, **kwargs)

    def spiders_search(self, value):
        """
        The function that pushes (key, value) to redis list, where key is spider_name:start_urls and value is user's search phrase.

        @param value: the phrase for spiders to search.
        @return:
        """
        for spider in SPIDERS:
            query = "{}:start_urls".format(spider)
            r = redis.StrictRedis()
            r.rpush(query, value)

    def get_finished_tasks(self, user, **kwargs):
        """
        The function that gets all finished tasks for current user.

        @param user: current user or None for anonymous user.
        @return: last ten tasks
        """
        tasks = Tasks.objects.all().filter(user=user, status=FINISHED).order_by('pk')
        tasks = Tasks.objects.filter(pk__in=tasks).distinct('keyword')
        return reversed(sorted(tasks, key=byID, reverse=True)[:10])

    def generate_task_number(self):
        """
        Each search has it's own task_number. The function increases last tasks's number by one on returns 0 if it is
        the first task.

        :return: next task number.
        """
        try:
            task_number = Tasks.objects.latest('task_number').task_number + 1
        except:
            task_number = 0
        return task_number

    def get_task_number(self, user_id, keyword):
        """
        The function returns task_number for current user's search.

        :param user_id: current user's id.
        :param keyword: current user's search phrase.
        :return: task number.
        """
        task = Tasks.objects.filter(user_id=user_id, keyword=keyword)[0]
        return task.task_number

    def save_task(self, task, value, task_number):
        """
        The function that saves the new task to database.

        @param task: task to save.
        @param value: search phrase.
        @param task_number: task number
        """
        task.status = START_STATUS
        task.keyword = value
        task.task_number = task_number
        task.save()
        Results.objects.filter(task=task).delete()

    def normalize_value(self, value):
        """
        The function that deletes all symbols from the string except digits, letters and spaces. Also it cuts all spaces
        in the beginning and at the end of the string.

        @param value: the search phrase that should be normalized.
        @return: normalized string.
        """
        q = re.compile(r'[^a-zA-Z0-9_ ]')
        res = q.sub('', value)
        return res.strip()

    def post(self, request, *args, **kwargs):
        """
        POST method.

        The function creates a new Task or gets an existing one for current user, his search phrase and the reserched site.
        If the Task is created or older than one day, the spiders_search method is called.
        """

        if request.user.is_authenticated():
            user = request.user
            user_pk = request.user.pk
        else:
            user = None
            user_pk = -1
        value = self.normalize_value(request.POST.get('search', ""))
        if value == "":
            return HttpResponse("-1")

        task_number = self.generate_task_number()
        r = redis.StrictRedis()
        if r.get({str(user_pk):value}) is not None:
            task_number = r.get({str(user_pk):value})
            return HttpResponse(json.dumps({'task_number':task_number.decode('utf8')}))

        r.set({str(user_pk):value}, task_number)

        task_google, created = Tasks.objects.get_or_create(keyword=value, user=user, site="google")
        task_yandex, created = Tasks.objects.get_or_create(keyword=value, user=user, site="yandex")
        task_instagram, created = Tasks.objects.get_or_create(keyword=value, user=user, site="instagram")
        r.delete({str(user_pk): value})
        one_day = timedelta(days=1)
        if created or task_google.date + one_day < datetime.date(datetime.now()) or task_google.status == START_STATUS\
                or task_yandex.status == START_STATUS or task_instagram.status == START_STATUS:

            self.save_task(task_google, value, task_number)
            self.save_task(task_yandex, value, task_number)
            self.save_task(task_instagram, value, task_number)
            value = json.dumps({'value': value, 'user':user_pk})
            self.spiders_search(value)
            logger.debug('Task number '+str(task_number))
            return HttpResponse(json.dumps({'task_number':str(task_number)}))
        else:
            logger.debug("({}) already in database".format(value))
            return HttpResponse(json.dumps({'search_phrase':value}))


    def get(self, request, *args, **kwargs):
        """
        GET method.

        The functions gets all 'finished' tasks and transfer them into context.
        """
        if request.user.is_authenticated():
            user = request.user
        else:
            user = None
        finished_tasks = self.get_finished_tasks(user)

        return render(request, 'index.html', {'tasks':finished_tasks})



class LoginView(FormView):
    template_name = 'login.html'
    form_class = LoginForm

    def form_valid(self, form):
        user = form.get_authenticated_user()
        login(self.request, user)
        return HttpResponseRedirect('/')


class LogoutView(View, LoginRequiredMixin):
    redirect_field_name = '/login/'
    def get(self, request):
        logout(self.request)
        return HttpResponseRedirect('/')


class RegisterView(FormView):
    form_class = RegistrationForm
    template_name = 'register.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return HttpResponseRedirect('/')


class Authorize(View):
    def get(self, request):
        return HttpResponseRedirect('https://oauth.yandex.ru/authorize?response_type=code&client_id=28b5af656ea54530aa225aeb66123129&force_confirm=yes')


class Verification(View):
    def get(self, request):



        r = requests.post('https://oauth.yandex.ru/token', data={'grant_type':'authorization_code','code':str(request.GET.get('code', '')),
                                                                 'client_id':'28b5af656ea54530aa225aeb66123129', 'client_secret':'cb7fe3ba115f45ccbe35e391fc0d187d'})

        if 'access_token' in r.json().keys():
            access_token = r.json()['access_token']
            stri = "min=" + str(int(r.json()['expires_in'])/60) + " hours=" + str(int(r.json()['expires_in'])/360)
           # return HttpResponse(stri)
            return HttpResponseRedirect('/upload_to_yandex_drive/'+access_token)
        else:
            return HttpResponseRedirect('/authorize/')


def UploadToYandexDrive(request, token):
    # resp = send_file(request)
    # return HttpResponse(resp.content)


    # if not request.user.is_authenticated():
    #     user = "[-1]"
    # else:
    #     user = '['+str(request.user.pk)+']'
    #
    # download_photos(user)
    # path = settings.PIC_DIR+user+'/'
    #
    # filenames = os.listdir(path)
    # zip_subdir = "files"
    # zip_filename = "%s.zip" % zip_subdir
    #
    # s = BytesIO()
    # zf = zipfile.ZipFile(s, "w")
    #
    # for fpath in filenames:
    #     zip_path = os.path.join(zip_subdir, fpath)
    #     zf.write(path+fpath, zip_path)
    # zf.close()


   # filepath = settings.PIC_DIR + '[-1]/http:im3-tub-ua.yandex.neti?id=9b6fec984f9d943dcd9a1527b4cc2488&amp;n=33&amp;h=215&amp;w=220'
    filepath='/home/user/Projects/[-1].tar.gz'

    with open(filepath, 'rb') as fh:

        mydata='hello'
        import hashlib
        hash_object = hashlib.sha256(mydata.encode('utf-8'))
        hex_dig = hash_object.hexdigest()
        response = requests.get('https://cloud-api.yandex.net/v1/disk/resources/upload?url=https://disk.yandex.ua/client/disk&path=b', headers={'Authorization': 'OAuth ' +token})

        if 'href' in response.json():
            href = response.json()['href']
        else:
            href = response.json()
       # response2 = requests.post(href, files=files, headers={'Authorization': 'OAuth ' +token})
        response2 = requests.put(href,
                                 data=fh,
                                 headers={'Authorization': 'OAuth ' +token})




       # response = requests.put('https://webdav.yandex.ru/filename.conf',
        #                        data=mydata,
       #                         headers={'Content-Type': 'application/binary', 'Authorization': 'OAuth ' +token, 'Content-Length':str(os.path.getsize(filepath)),
        #                                 'Sha256': hex_dig,})


    return HttpResponse(token + "++++++++++++" +response.text + "++++++++++++" + hex_dig+ "++++++++++++++++++++++"+response2.text)




def download_photos(user):
    import boto
    from django.conf import settings
    import os
    print("downloading")
    conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    bucket = conn.get_bucket(bucket_name)
    path = ""
    for key in bucket.list():
        print(key)
        if user == key.name.split("/")[0] and key.name.split("/")[1]!="":
             path = settings.PIC_DIR + user + "/"
             print(user,path)
             os.makedirs(path, exist_ok=True)
             key.get_contents_to_filename( path + (key.name.split("/")[1]))
  #  to_zip (path, user)


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



def send_file(request):
    if not request.user.is_authenticated():
        user = "[-1]"
    else:
        user = '['+str(request.user.pk)+']'

    download_photos(user)
    path = settings.PIC_DIR+user+'/'

    filenames = os.listdir(path)
    zip_subdir = "files"
    zip_filename = "%s.zip" % zip_subdir

    s = BytesIO()
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        zip_path = os.path.join(zip_subdir, fpath)
        zf.write(path+fpath, zip_path)
    zf.close()


    resp = HttpResponse(s.getvalue(), content_type="application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp


# def send_file(request):
#   import os, tempfile, zipfile
#   from wsgiref.util import FileWrapper
#   from django.conf import settings
#   import mimetypes
#
#   filename     = settings.PIC_DIR+'None.zip' # Select your file here.
#   download_name ="example.zip"
#   wrapper      = FileWrapper(open(filename))
#   content_type = mimetypes.guess_type(filename)[0]
#   response     = HttpResponse(wrapper,content_type=content_type)
#   response['Content-Length']      = os.path.getsize(filename)
#   response['Content-Disposition'] = "attachment; filename=%s"%download_name
#   return response


