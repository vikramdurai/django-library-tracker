from django.conf.urls import url, include

from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^$', views.index, name="index"),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^oauth/', include('social_django.urls', namespace='social')),
    url(r'^search$', views.search, name="search"),
    url(r'^borrowed$', views.view_books, name="borrowed_books"),
    url(r'^titles/(?P<slug>[-\w\d]+)/book/(?P<acc>[-\w\d]+)/$',
        views.view_one_book, name="titles"),
    url(r'^extend/(?P<slug>[-\w\d]+)/book/(?P<acc>[-\w\d]+)/$',
        views.extend, name="extend")
]
