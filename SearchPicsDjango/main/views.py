from django.shortcuts import render
from django.views.generic import TemplateView, View, FormView
from django.http import HttpResponse,JsonResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin

from datetime import datetime, timedelta
import re
import json
import redis
import logging
logger = logging.getLogger(__name__)

from .models import Results, Tasks
from .forms import LoginForm, RegistrationForm

SPIDERS = ['google', 'yandex', 'instagram']
START_STATUS = "IN_PROGRESS yandex google instagram"
FINISHED = "FINISHED"


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

        Gets all results for current user by his search phrase and sorts them by id.
        """
        if request.user.is_authenticated():
            task = Tasks.objects.filter(keyword=kwargs['phrase'], user=request.user)
        else:
            task = Tasks.objects.filter(keyword=kwargs['phrase'], user=None)
        pics = Results.objects.filter(task=task)
        pics = sorted(pics, key=byRank)
        return render(request, 'search.html', {'pics':pics})


class MainView(TemplateView):
    """
    Class MainView.
    """
    template_name = "index.html"

    def spiders_search(self, value):
        """
        The function that pushes key value to redis list, where key is spider_name:start_urls and value is user's search phrase.

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
        @return: tasks, sorted by id.
        """
       # tasks = Tasks.objects.filter(user=user, status=FINISHED)
        tasks = Tasks.objects.filter(user=user, status=FINISHED)
        return reversed(sorted(tasks, key=byID, reverse=True)[:10])

    def save_task(self, task, value):
        """
        The function that saves the new task to database.

        @param task: task to save.
        @param value: search phrase.
        """
        task.status = START_STATUS
        task.keyword = value
        task.save()

    def normalize_value(self, value):
        """
        The function that deletes all symbols from the string except digits, letters and spaces.

        @param value: the search phrase that should be normalized.
        @return: normalized string.
        """
        q = re.compile(r'[^a-zA-Z0-9_ ]')
        res = q.sub('', value)
        return res.rstrip()

    def post(self, request, *args, **kwargs):
        """
        POST method.

        The function creates a new Task or gets an existing one for current user and his search phrase.
        If the Task is created or older than one day, the spiders_search method is called.
        The database saves history of researches only for registered users.
        The functions gets separately all 'finished' and 'in progress' tasks and transfer them into context.
        """
        if request.user.is_authenticated():
            user = request.user
            user_pk = request.user.pk
        else:
            user = None
            user_pk = -1
        value = self.normalize_value(request.POST.get('search', ""))
        finished_tasks = self.get_finished_tasks(user)
        if value == "":
            return render(request, 'index.html', {'tasks': finished_tasks})
        task, created = Tasks.objects.get_or_create(keyword=value, user=user)
        one_day = timedelta(days=1)
        if created or task.date + one_day < datetime.date(datetime.now()):
            self.save_task(task, value)
            value = json.dumps({'value': value, 'user':user_pk})
            self.spiders_search(value)

        finished_tasks = self.get_finished_tasks(user)
        return render(request, 'index.html', {'tasks': finished_tasks})

    def get(self, request, *args, **kwargs):
        """
        GET method.

        The functions gets separately all 'finished' and 'in progress' tasks and transfer them into context.
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
