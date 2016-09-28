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
logger = logging.getLogger(__name__)

from .models import Results, Tasks
from .forms import LoginForm, RegistrationForm

SPIDERS = ['google', 'yandex', 'instagram']
#START_STATUS = "IN_PROGRESS yandex google instagram"
START_STATUS = "IN_PROGRESS"
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
            tasks = Tasks.objects.filter(keyword=kwargs['phrase'], user=request.user)
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
        @return: last ten tasks
        """
        #tasks = Tasks.objects.order_by('keyword', '-id').distinct('keyword').values_list('id', flat=True)
        tasks = Tasks.objects.all().filter(user=user, status=FINISHED).order_by('-id')
        print(tasks)
        print(tasks.query)
        tasks = Tasks.objects.filter(pk__in=tasks).distinct('keyword')
        #tasks = Tasks.objects.filter(pk__in=tasks).filter(user=user, status=FINISHED).order_by('-id')
        print(tasks)
        print(tasks.query)
        return sorted(tasks[:10], key=byID)


    def save_task(self, task, value):
        """
        The function that saves the new task to database.

        @param task: task to save.
        @param value: search phrase.
        """
        task.status = START_STATUS
        task.keyword = value
        task.save()
        Results.objects.filter(task=task).delete()

    def normalize_value(self, value):
        """
        The function that deletes all symbols from the string except digits, letters and spaces.

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
        print(request.POST)
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
        task_google, created = Tasks.objects.get_or_create(keyword=value, user=user, site="google")
        task_yandex, created = Tasks.objects.get_or_create(keyword=value, user=user, site="yandex")
        task_instagram, created = Tasks.objects.get_or_create(keyword=value, user=user, site="instagram")
        one_day = timedelta(days=1)
        if created or task_google.date + one_day < datetime.date(datetime.now()) or task_google.status == START_STATUS\
                or task_yandex.status == START_STATUS or task_instagram.status == START_STATUS:
            self.save_task(task_google, value)
            self.save_task(task_yandex, value)
            self.save_task(task_instagram, value)
            value = json.dumps({'value': value, 'user':user_pk})
            self.spiders_search(value)
        else:
            print("({}) already in database".format(value))
            finished_tasks = self.get_finished_tasks(user)
            task_on_screen = False
            # for task in finished_tasks:
            #     if value in task.keyword:
            #         task_on_screen = True
            #         print("({}) already on screen".format(value))
            #         break
            if not task_on_screen:
                print("({}) not on screen".format(value))
                if user:
                    user_id = user.id
                else:
                    user_id = -1
                r = redis.StrictRedis(host='localhost', port=6379, db=0)
                message = json.dumps({'search_phrase': value, 'user_id': user_id, 'was_searched_before':True})
                r.publish('our-channel', message)
                print("Django sent message({}) to webserver".format(message))

        finished_tasks = self.get_finished_tasks(user)
        return render(request, 'index.html', {'tasks': finished_tasks})

    def get(self, request, *args, **kwargs):
        """
        GET method.

        The functions gets separately all 'finished' tasks and transfer them into context.
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
