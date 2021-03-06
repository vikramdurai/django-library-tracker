from django.conf.urls import url, include

from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^$', views.index, name="index"),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^oauth/', include('social_django.urls', namespace='social')),
    url(r'^search/', views.search, name="search"),
    url(r'^checkin-a-book', views.view_books, name="borrowed_books"),
    url(r'^titles/(?P<slug>[-\w\d]+)/book/(?P<acc>[-\w\d]+)/$',
        views.view_one_book, name="titles"),
    url(r'^extend/(?P<slug>[-\w\d]+)/book/(?P<acc>[-\w\d]+)/$',
        views.extend, name="extend"),
    url(r'^checkout/$',
        views.checkout, name="checkout"),
    url(r'^checkin/(?P<slug>[-\w\d]+)/book/(?P<acc>[-\w\d]+)/$',
        views.checkin, name="checkin"),
    url(r'^addstaff', views.addstaff, name="addstaff"),
    url(r'^newbook', views.new_book, name="newbook"),
    url(r'^newpublication', views.new_publication, name="newpublication"),
    # url(r'^userconfig', views.userconfig, name="userconfig"),
    url(r'^bye-bye', views.bye_bye, name="bye_bye"),
    url(r'^pending-requests', views.pending_requests, name="pendingrequests"),
    url(r'^approve-request', views.approve_requests, name="approverequest"),
    url(r'^apisearch', views.api_search, name="apisearch"),
    url(r'^api_get_borrowed_books', views.api_view_borrowed_books,
        name="api_get_borrowed_books"),
    url(r'^exportdata', views.export_data, name="exportdata"),
    url(r'^api_homepage', views.api_homepage, name="api_homepage")
]
