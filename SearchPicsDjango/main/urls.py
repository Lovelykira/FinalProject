from django.conf.urls import url

from .views import *

urlpatterns = [
    url(r'search/(?P<id>\w+)/(?P<phrase>.+)/$', SearchView.as_view()),
    url(r'^$', MainView.as_view()),
    url(r'^login/$', LoginView.as_view()),
    url(r'^logout/$', LogoutView.as_view()),
    url(r'^register/$', RegisterView.as_view()),
    url(r'^download/$', send_file),
    url(r'^authorize/$', Authorize.as_view()),
    url(r'^verification_code/$', Verification.as_view()),
    url(r'^upload_to_yandex_drive/(?P<token>.+)/$', UploadToYandexDrive),
]