from django.shortcuts import render
from django.views.generic import TemplateView, View, FormView
from django.http import HttpResponse,JsonResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import re
import json
import redis
import logging
import requests
import boto
import zipfile
import os

from django.conf import settings
from io import StringIO, BytesIO
from datetime import datetime, timedelta
from xml.dom import minidom

from .models import Results, Tasks, UserToken
from .forms import LoginForm, RegistrationForm

SPIDERS = ['google', 'yandex', 'instagram']
START_STATUS = "IN_PROGRESS"
FINISHED = "FINISHED"

logger = logging.getLogger(__name__)


def byRank(item):
    """
    Key to sort Result objects.
    :param item: Result object.
    :return:
    """
    return item.rank


def byID(item):
    """
    Key to sort Task objects.
    :param item: Task object.
    :return:
    """
    return item.id


def normalize_value(value):
    """
    The function that deletes all symbols from the string except digits, letters and spaces. Also it cuts all spaces
    in the beginning and at the end of the string.

    @param value: the search phrase that should be normalized.
    @return: normalized string.
    """
    q = re.compile(r'[^a-zA-Z0-9_ ]')
    res = q.sub('', value)
    return res.strip()


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
            tasks = Tasks.objects.filter(keyword=kwargs['keyword'], user_id=str(kwargs['id']))
        else:
            tasks = Tasks.objects.filter(keyword=kwargs['keyword'], user=None)
        pics = Results.objects.filter(task__in=tasks)
        pics = sorted(pics, key=byRank)
        return render(request, 'search.html', {'pics':pics, 'keyword':kwargs['keyword']})


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
        value = normalize_value(request.POST.get('search', ""))
        if value == "":
            return HttpResponseRedirect("/")

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
        """
        GET method.

        The function that redirects to oauth.yandex for user to confirm allowing access to account.
        :param request:
        :return: HttpResponseRedirect to oauth.yandex with parameters response_type='code', client_id=registered app client id
        and force_confirm='yes'.
        """
        if request.user.is_authenticated():
            user = request.user
        else:
            user = None
        try:
            ut = UserToken.objects.get(user=user, uuid=request.sessions.get('uuid', ''))
            if ut.expire_time >= datetime.now():
                return HttpResponseRedirect('/upload_to_yandex_drive/' + '?keyword=' + request.GET.get('keyword', ''))
        except: #finally
            return HttpResponseRedirect('https://oauth.yandex.ru/authorize?response_type=code&client_id={}&force_confirm=yes&state={}'.format(settings.YANDEX_APP_CLIENT_ID, request.GET.get('keyword', '')))


class Verification(View):
    def get(self, request):
        """
        GET method.

        This view maintains the callback ulr from oauth.yandex. Verification code was sent as 'code' parameter.
        This function posts this code and app's client id and password to oauth.yandex/token to get access_token and then
        if everything went ok, redirects to /upload_to_yandex_drive/.
        :param request:
        :return: HttpResponseRedirect to /upload_to_yandex_drive/ if everything went ok and
                HttpResponseRedirect to /authorize/ if access token wasn't sent for some reason.
        """
        keyword = request.GET.get('state', '')
        r = requests.post('https://oauth.yandex.ru/token', data={'grant_type':'authorization_code','code':str(request.GET.get('code', '')),
                                                                 'client_id':settings.YANDEX_APP_CLIENT_ID, 'client_secret':settings.YANDEX_APP_CLIENT_PASS})

        if request.user.is_authenticated():
            user = request.user
        else:
            user = None

        if 'access_token' in r.json().keys() and 'expires_in' in r.json().keys():
            access_token = r.json()['access_token']
            UserToken.objects.create(user=user, uuid=request.session.get('uuid', ''), token=access_token, expire_time=datetime.now()+timedelta(seconds=r.json()['expires_in']))

            return HttpResponseRedirect('/upload_to_yandex_drive/' + '?keyword=' + keyword)
        else:
            return HttpResponseRedirect('/authorize/')


def upload_to_YandexDrive(request):
    """
    This function uploads pictures to YandexDrive.

    First it's downloading pictures from AWS S3 and then uploads it one by one to user's yandex disk using access_token.
    Notice that if file was created earlier it will not be overwritten.
    :param request:
    :param token: access token, which has been gotten in Verification view.
    :return: HttpResponseRedirect to previous page - /search/user_id/keyword/
    """


    if request.user.is_authenticated():
        user = "[{}]".format(request.user.pk)
        user_pk = request.user
    else:
        user = "[-1]"
        user_pk = None
    keyword = request.GET.get('keyword', '')
    download_photos_from_aws(user, keyword)

    ut = UserToken.objects.get(user=user_pk, uuid=request.session.get('uuid', ''))
    token = ut.token

    r = requests.request('PROPFIND', 'http://webdav.yandex.ru',
                         headers={'Authorization': 'OAuth ' + token, 'depth':'1'})
    xmldoc = minidom.parseString(r.text)
    itemlist = xmldoc.getElementsByTagName('d:displayname')
    yandex_filenames = []
    for child in itemlist:
        yandex_filenames.append(str(child.firstChild.nodeValue))


    path = settings.PIC_DIR + user + "/" + keyword + '/'
    filenames = os.listdir(path)
    filenames = [path+filename for filename in filenames]

    for filepath in filenames:
        with open(filepath, 'rb') as fh:
            filepath = normalize_value(filepath)
            i=1
            while True:
                if filepath in yandex_filenames:
                    filepath = "{} ({})".format(filepath, i)
                else:
                    break
            response = requests.get('https://cloud-api.yandex.net/v1/disk/resources/upload?url=https://disk.yandex.ua/client/disk&path='+filepath, headers={'Authorization': 'OAuth ' +token})

            if 'href' in response.json():
                href = response.json()['href']
            else:
                continue

            response2 = requests.put(href,
                                    data=fh,
                                    headers={'Authorization': 'OAuth ' +token})
    return HttpResponseRedirect('/search/'+request.session.get('user', '')+'/'+keyword+'/')


def download_photos_from_aws(user, keyword):
    """
    The function that downloads pictures from aws.

    This function checks all keys in specified bucket and if one has /user_id/keyword as it's prefix, the function
    downloads it.
    :param user: user's id in format: '[user_id]'.
    :type: string.
    :param keyword: search phrase user is looking for.
    :type string.
    """
    conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    bucket = conn.get_bucket(bucket_name)

    path = settings.PIC_DIR + user + "/" + keyword + '/'
    os.makedirs(path, exist_ok=True)
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.error(e)

    for key in bucket.list():
        logger.debug(key)
        prefix = key.name.split("/")
        if user == prefix[0] and keyword == prefix[1] and key.name.split("/")[2]!="":
             logger.debug("OK")
             key.get_contents_to_filename( path + (key.name.split("/")[2]))


def send_zip_file(request, id, keyword):
    """
    The function that sends zip file with requested pictures to user.

    This function gets all files in path specified as ../user_id/searched_phrase/ compresses them one by one to
    zip file and sends it to user.
    :param request:
    :return:
    """
    # if request.user.is_authenticated():
    #     user = "[{}]".format(request.user.pk)
    # else:
    #     user = "[-1]"
    # keyword = request.get('keyword', '')
    user = "[{}]".format(id)
    download_photos_from_aws(user, keyword)
    path = settings.PIC_DIR+user+'/' + keyword + '/'
    filenames = os.listdir(path)

    s = BytesIO()
    zf = zipfile.ZipFile(s, "w")
    for fpath in filenames:
        zf.write(path+fpath, fpath)
    zf.close()
    zip_filename = 'files'
    resp = HttpResponse(s.getvalue(), content_type="application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename
    return resp
