from django.urls import path
from . import views


app_name = 'whatsnew'
urlpatterns = [
    path('feed.rss', views.feed_rss, name='feed_rss'),
]
