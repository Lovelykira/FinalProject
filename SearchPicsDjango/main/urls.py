from django.conf.urls import url

from .views import *

urlpatterns = [
    url(r'search/(?P<id>\w+)/(?P<keyword>.+)/$', SearchView.as_view()),
    url(r'^$', MainView.as_view()),
    url(r'^login/$', LoginView.as_view()),
    url(r'^logout/$', LogoutView.as_view()),
    url(r'^register/$', RegisterView.as_view()),
    url(r'^download/(?P<id>\w+)/(?P<keyword>.+)/$', send_zip_file),
    url(r'^authorize/$', Authorize.as_view()),
    url(r'^verification_code/$', Verification.as_view()),
    url(r'^upload_to_yandex_drive/$', upload_to_YandexDrive),
]