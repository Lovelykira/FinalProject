from django.test import TestCase, RequestFactory
from django.test import Client
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware

from mock import patch, sentinel, Mock

from .models import Tasks, Results
from .views import MainView, SearchView, LogoutView, LoginView, RegisterView


class TestCalls(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='jacob', password='top_secret')
        self.value = 'test'
        task = Tasks.objects.create(keyword=self.value, status='FINISHED', user=self.user)
        Results.objects.create(task=task, link='', img='', rank=1, site='google')

    def test_logout_view(self):
        request = self.factory.get('/logout/')
        request.user = self.user
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        response = LogoutView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(type(request.user), AnonymousUser)

    def test_login_view(self):
        request = self.factory.post('/login/', {'username':'jacob', 'password':'top_secret'})
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        response = LoginView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(request.user.username, 'jacob')

    def test_register_view(self):
        request = self.factory.post('/register/', {'username': 'sam', 'password1': 'secret', 'password2': 'secret'})
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        response = RegisterView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(request.user.username, 'sam')

    def test_search_view(self):
        self.client.login(username='jacob', password='top_secret')
        response = self.client.get('/search/{}/'.format(self.value))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context[-1]['pics']), 1)

    def test_main_view(self):
        request = self.factory.get('/')
        request.user = self.user
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        response = MainView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        self.client.login(username='jacob', password='top_secret')
        response = self.client.get('/')
        self.assertEqual(len(response.context[-1]['tasks']), 1)

        request = self.factory.post('/', {'search': 'new_value'})
        request.user = self.user
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        response = MainView.as_view()(request)
        self.assertEqual(response.status_code, 200)
