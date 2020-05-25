from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('daily-text/', include('wtpodcast2.feeds.dailytext.urls')),
    path('magazines/', include('wtpodcast2.feeds.magazines.urls')),
    path('whats-new/', include('wtpodcast2.feeds.whatsnew.urls')),
]

if settings.DEBUG:
    urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + urlpatterns
