from django.templatetags.static import static
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from feedgen.feed import FeedGenerator
from .models import Article


def get_feed(request):
    fg = FeedGenerator()
    fg.load_extension('podcast')
    fg.podcast.itunes_category('Religion & Spirituality', 'Christianity')
    fg.podcast.itunes_image(request.build_absolute_uri(static('whatsnew/icon.png')))
    # fg.id(request.build_absolute_uri())
    fg.title("JW.ORG - What's New")
    fg.description("See what has been recently added to jw.org, the official website of Jehovah's Witnesses.")
    fg.link(href=request.build_absolute_uri(), rel='self')
    # Include all articles with audio in the past 30 days
    date_threshold = timezone.now() - timedelta(days=30)
    articles = Article.objects\
        .filter(pub_date__gte=date_threshold)\
        .filter(audio_file_link__isnull=False)\
        .all()
    for article in articles:
        fe = fg.add_entry()
        fe.id(article.guid)
        fe.title(article.title)
        fe.description(article.description)
        fe.updated(article.pub_date)
        fe.published(article.pub_date)
        fe.enclosure(article.audio_file_link, str(article.audio_file_duration), article.audio_file_mimetype)
        fe.link(href=article.audio_file_link, type=article.audio_file_mimetype)
    return fg


def feed_rss(request):
    fg = get_feed(request)
    return HttpResponse(fg.rss_str(pretty=False), content_type='application/rss+xml')
