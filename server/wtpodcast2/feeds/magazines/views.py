from django.templatetags.static import static
from django.http import HttpResponse
from feedgen.feed import FeedGenerator
from .models import Issue


def get_feed(request):
    fg = FeedGenerator()
    fg.id(request.build_absolute_uri())
    fg.load_extension('podcast')
    fg.podcast.itunes_category('Religion & Spirituality', 'Christianity')
    fg.podcast.itunes_image(request.build_absolute_uri(static('magazines/icon.png')))
    fg.title("JW.ORG Magazines")
    fg.description("Combined Feed of Watchtower (public), Watchtower (study), and Awake! in English from jw.org.")
    fg.link(href=request.build_absolute_uri(), rel='self')
    # Include all issues
    for issue in Issue.objects.all():
        audio_url = request.build_absolute_uri(issue.audio_file.url)
        fe = fg.add_entry()
        fe.id(audio_url)
        fe.title(issue.name)
        fe.description(issue.name)
        fe.updated(issue.imported)
        fe.published(issue.imported)
        fe.enclosure(audio_url, str(issue.audio_file_duration), 'audio/mpeg')
        fe.link(href=audio_url, type='audio/mpeg')
    return fg


def feed_atom(request):
    fg = get_feed(request)
    return HttpResponse(fg.atom_str(pretty=True), content_type='application/atom+xml')


def feed_rss(request):
    fg = get_feed(request)
    return HttpResponse(fg.rss_str(pretty=True), content_type='application/rss+xml')
