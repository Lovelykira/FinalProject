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

from .models import Results, Tasks
from .forms import LoginForm, RegistrationForm

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
