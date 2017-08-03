from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.sony, name='index'),
    url(r'^sony$', views.sony, name='index'),
    url(r'^samsung$', views.samsung, name='index'),
]