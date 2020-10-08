from datetime import timedelta
from dateutil.parser import parse as parse_date
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.conf import settings
from pydub import AudioSegment
import eyed3
import os.path
import requests
import pytz
import tempfile


class Issue(models.Model):
    pub = models.CharField(max_length=10)
    pub_name = models.CharField(max_length=50)
    issue_date = models.CharField(max_length=50)
    formatted_issue_date = models.CharField(max_length=100)
    cover_image = models.ImageField(upload_to='magazine-cover/', null=True)

    audio_file = models.FileField(upload_to='magazine-issues/', null=True)
    audio_file_duration = models.PositiveIntegerField(null=True)

    imported = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issue_date', 'pub_name', '-pk']
        unique_together = [
            ('pub', 'issue_date'),
        ]


    @classmethod
    def import_new(cls, pubs=['g', 'w', 'wp']):
        today = timezone.now()
        months = (today + timedelta(days=m * 30) for m in range(12))
        issue_dates = (m.strftime('%Y%m') for m in months)
        for issue_date in issue_dates:
            for pub in pubs:
                try:
                    cls.import_issue(pub, issue_date)
                except Exception as e:
                    print(e)


    @classmethod
    def import_issue(cls, pub, issue_date):
        language = 'E'
        fileformat = 'MP3'
        try:
            resp = requests.get('https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS', params={
                'pub': pub,
                'issue': issue_date,
                'output': 'json',
                'fileformat': fileformat,
                'alllangs': 0,
                'langwritten': language,
                'txtCMSLang': language,
            })
            resp.raise_for_status()
        except requests.RequestException:
            return
        data = resp.json()
        # Set basic issue info
        issue = cls.objects.filter(pub=pub, issue_date=issue_date).first()
        if issue is None:
            issue = cls(pub=pub, issue_date=issue_date)
        issue.pub_name = data['pubName']
        issue.formatted_issue_date = data['formattedDate']
        issue.save()
        # Save cover image
        issue.save_cover(data['pubImage']['url'])
        print(issue)
        # Save articles
        for article_data in data['files'][language][fileformat]:
            if article_data['mimetype'] == 'application/zip':
                continue
            issue.save_article(article_data)
        # Create combined audio file
        issue.create_combined_audio()


    @property
    def name(self):
        return mark_safe(f'{self.pub_name} {self.formatted_issue_date}')


    def save_cover(self, cover_url):
        if self.cover_image is not None:
            return
        try:
            resp = requests.get(cover_url, stream=True)
            resp.raise_for_status()
        except requests.RequestException:
            return
        resp.raw.decode_content = True
        self.cover_image.save(name=os.path.basename(cover_url), content=resp.raw)
        self.save()


    def save_article(self, data):
        article = Article.objects.filter(issue=self, track=data['track']).first()
        if article is not None:
            return
        article = Article(issue=self, track=data['track'])
        article.mid = data['docid']
        article.title = data['title']
        modified = parse_date(data['file']['modifiedDatetime']).replace(tzinfo=pytz.UTC)
        article.modified = modified
        article.audio_file_link = data['file']['url']
        article.audio_file_duration = data['duration']
        article.audio_file_bitrate = data['bitRate']
        article.audio_file_mimetype = data['mimetype']
        article.download_audio()
        article.save()


    def create_combined_audio(self):
        if self.audio_file:
            return
        # Combine MP3 files into a single file
        combined = AudioSegment.empty()
        chapters = []
        _chap_start = 0
        _chap_end = 0
        for article in self.articles.order_by('track').all():
            _chap_end = _chap_start + (article.audio_file_duration * 1000)
            combined += AudioSegment.from_file(article.audio_file.file, format='mp3')
            chapters.append((article.title, int(_chap_start), int(_chap_end)))
            _chap_start = _chap_end
        # Export the new combined file
        with tempfile.NamedTemporaryFile() as fp:
            combined.export(fp.name, format='mp3', bitrate="128k")
            id3 = eyed3.load(fp.name)
            # Extract the cover image from the first article MP3
            first_article_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, self.articles.first().audio_file.name))
            cover_id3 = eyed3.load(first_article_path)
            if cover_id3 is not None:
                cover_img_frame = cover_id3.tag.images.get('')
                # Set cover image on combined file
                id3.tag.images._fs[b'APIC'] = cover_img_frame
            # Add chapter markers to the combined file
            index = 0
            child_ids = []
            for chapter in chapters:
                element_id = ("chp{}".format(index)).encode()
                title, start_time, end_time = chapter
                new_chap = id3.tag.chapters.set(element_id, (start_time, end_time))
                new_chap.sub_frames.setTextFrame(b"TIT2", "{}".format(title))
                child_ids.append(element_id)
                index += 1
            id3.tag.table_of_contents.set(b"toc", toplevel=True, ordered=True, child_ids=child_ids)
            # Display issue info
            print("%s: Created combined audio with length of %s seconds" % (self, combined.duration_seconds))
            print("%s" % self)
            for chap in id3.tag.chapters:
                print("%s:  - %s" % (self, chap.sub_frames.get(b"TIT2")[0]._text))
            # Save ID3 tags
            id3.tag.save()
            # Save the combined file somewhere permanent
            self.audio_file_duration = combined.duration_seconds
            self.audio_file.save(content=fp, name=f'{self.pub}_E_{self.issue_date}.mp3')
        self.save()


    def __str__(self):
        return f'Issue[pub={self.pub}, issue={self.formatted_issue_date}]'




class Article(models.Model):
    issue = models.ForeignKey(Issue,
        related_name='articles',
        on_delete=models.CASCADE)
    track = models.PositiveIntegerField()

    mid = models.CharField(max_length=50)
    title = models.TextField()
    modified = models.DateTimeField()

    audio_file_link = models.URLField()
    audio_file_duration = models.PositiveIntegerField()
    audio_file_bitrate = models.PositiveIntegerField()
    audio_file_mimetype = models.CharField(max_length=50)

    audio_file = models.FileField(upload_to='magazine-articles/', null=True)

    imported = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issue', 'track', 'pk']
        unique_together = [
            ('issue', 'track'),
        ]


    def download_audio(self):
        try:
            resp = requests.get(self.audio_file_link, stream=True)
            resp.raise_for_status()
        except requests.RequestException:
            return
        resp.raw.decode_content = True
        self.audio_file.save(name=os.path.basename(self.audio_file_link), content=resp.raw)
        self.save()


    def __str__(self):
        return f'Article[title={self.title}]'
