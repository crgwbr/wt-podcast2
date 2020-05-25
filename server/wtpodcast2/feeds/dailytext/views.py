from django.templatetags.static import static
from django.http import HttpResponse
from django.utils import timezone
from feedgen.feed import FeedGenerator
from .models import DailyTextEntry


def get_feed(request):
    fg = FeedGenerator()
    fg.id(request.build_absolute_uri())
    fg.load_extension('podcast')
    fg.podcast.itunes_category('Religion & Spirituality', 'Christianity')
    fg.podcast.itunes_image(request.build_absolute_uri(static('dailytext/icon.png')))
    fg.title("Examining the Scriptures Daily")
    fg.description("Daily feed of the Bible chapter for the day's daily text")
    fg.link(href=request.build_absolute_uri(), rel='self')
    # Include all issues
    for entry in DailyTextEntry.objects.filter(day__lte=timezone.now()).all():
        fe = fg.add_entry()
        day = entry.day.strftime('%b %-d, %Y')
        title = f'{day} – {entry.name}'
        fe.id(title)
        fe.title(title)
        fe.description(entry.content)
        fe.updated(entry.imported)
        fe.published(entry.imported)
        fe.enclosure(entry.audio_file_link, str(entry.audio_file_duration), 'audio/mpeg')
        fe.link(href=entry.audio_file_link, type='audio/mpeg')
    return fg


def feed_atom(request):
    fg = get_feed(request)
    return HttpResponse(fg.atom_str(pretty=True), content_type='application/atom+xml')


def feed_rss(request):
    fg = get_feed(request)
    return HttpResponse(fg.rss_str(pretty=True), content_type='application/rss+xml')
