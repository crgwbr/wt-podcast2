from django.db import models
from dateutil.parser import parse as parse_date
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import requests


class Article(models.Model):
    guid = models.CharField(max_length=50, unique=True)
    title = models.TextField()
    link = models.URLField()
    description = models.TextField()
    pub_date = models.DateTimeField()

    mid = models.CharField(max_length=50, null=True, blank=True)

    audio_file_link = models.URLField(null=True, blank=True)
    audio_file_duration = models.PositiveIntegerField(null=True, blank=True)
    audio_file_mimetype = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['-pub_date', '-pk']


    @classmethod
    def import_new(cls):
        resp = requests.get('https://www.jw.org/en/whats-new/rss/WhatsNewWebArticles/feed.xml')
        resp.raise_for_status()
        root = ElementTree.fromstring(resp.content)
        for channel in root.findall('channel'):
            for item in channel.findall('item'):
                print(cls.from_feed(item))


    @classmethod
    def from_feed(cls, item):
        # Set basic article info
        guid = item.find('guid').text
        article = cls.objects.filter(guid=guid).first()
        if article is not None and article.audio_file_link is not None:
            return article
        if article is None:
            article = cls(guid=guid)
        article.guid = item.find('guid').text
        article.title = item.find('title').text
        article.link = item.find('link').text
        article.description = item.find('description').text
        article.pub_date = parse_date(item.find('pubDate').text)
        article.save()
        article.load_mid()
        article.load_audio_file()
        return article


    def load_mid(self):
        resp = requests.get(self.link, headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36',
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, features="lxml")
        body = soup.find('body')
        body_id = body.get('id')
        if body_id.startswith('mid'):
            self.mid = body_id.replace('mid', '')
            self.save(update_fields=['mid'])


    def load_audio_file(self):
        if not self.mid:
            return
        try:
            resp = requests.get('https://apps.jw.org/GETPUBMEDIALINKS', params={
                'docid': self.mid,
                'output': 'json',
                'fileformat': 'MP3',
                'alllangs': 0,
                'track': 1,
                'langwritten': 'E',
                'txtCMSLang': 'E',
            })
            resp.raise_for_status()
        except requests.RequestException as e:
            print(e)
            return
        data = resp.json()
        try:
            file_data = data['files']['E']['MP3'][0]
            self.audio_file_link = file_data['file']['url']
            self.audio_file_duration = int(file_data['duration'])
            self.audio_file_mimetype = file_data['mimetype']
            self.save(update_fields=[
                'audio_file_link',
                'audio_file_duration',
                'audio_file_mimetype',
            ])
        except (IndexError, KeyError) as e:
            print(e)
            return
        return

    def __str__(self):
        return f'Article[title={self.guid}]'
