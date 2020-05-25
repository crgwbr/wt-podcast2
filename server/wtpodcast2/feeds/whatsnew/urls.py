from django.urls import path
from . import views


app_name = 'whatsnew'
urlpatterns = [
    path('feed.atom', views.feed_atom, name='feed_atom'),
    path('feed.rss', views.feed_atom, name='feed_rss'),
]