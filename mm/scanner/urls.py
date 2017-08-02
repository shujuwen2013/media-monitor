from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^sony$', views.index, name='index'),
    url(r'^samsung$', views.samsung, name='index'),
]