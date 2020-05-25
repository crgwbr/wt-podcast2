from django.core.management.base import BaseCommand
from wtpodcast2.feeds.dailytext.models import DailyTextEntry
from wtpodcast2.feeds.magazines.models import Issue
from wtpodcast2.feeds.whatsnew.models import Article


class Command(BaseCommand):
    def handle(self, *args, **options):
        DailyTextEntry.import_new()
        Issue.import_new()
        Article.import_new()
