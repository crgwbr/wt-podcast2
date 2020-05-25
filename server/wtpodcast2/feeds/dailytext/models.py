from datetime import date
from django.db import models
from bs4 import BeautifulSoup
import requests


class DailyTextEntry(models.Model):
    day = models.DateField(unique=True)
    content = models.TextField()

    name = models.CharField(max_length=100)
    book_num = models.PositiveIntegerField()
    chapter_num = models.PositiveIntegerField()
    verse_num = models.PositiveIntegerField()

    audio_file_link = models.URLField(null=True, blank=True)
    audio_file_duration = models.PositiveIntegerField(null=True, blank=True)
    audio_file_mimetype = models.CharField(max_length=50, null=True, blank=True)

    imported = models.DateTimeField(auto_now_add=True)


    @classmethod
    def import_new(cls):
        today = date.today()
        cls.import_day(today)


    @classmethod
    def import_day(cls, day):
        entry = cls.objects.filter(day=day).first()
        if entry is None:
            entry = cls(day=day)
        # Get text content
        year = day.strftime('%Y')
        month = day.strftime('%-m')
        day = day.strftime('%-d')
        try:
            resp = requests.get(f'https://wol.jw.org/wol/dt/r1/lp-e/{year}/{month}/{day}')
            resp.raise_for_status()
        except requests.RequestException:
            return
        data = resp.json()
        items = [i for i in data['items'] if 'Examining the Scriptures Daily' in i['publicationTitle']]
        if len(items) <= 0:
            return
        item = items[0]
        entry.content = '<div>%s</div>' % item['content']
        # Extract references
        soup = BeautifulSoup(entry.content, features="lxml")
        scripture_link_elem = soup.select_one('p.themeScrp a')
        scripture_link = scripture_link_elem['href']
        try:
            resp = requests.get(f'https://wol.jw.org{scripture_link}')
            resp.raise_for_status()
        except requests.RequestException:
            return
        verse_data = resp.json()['items'][0]
        entry.name = verse_data['title']
        entry.book_num = verse_data['book']
        entry.chapter_num = verse_data['first_chapter']
        entry.verse_num = verse_data['first_verse']
        entry.save()
        # Get audio data
        try:
            resp = requests.get('https://apps.jw.org/GETPUBMEDIALINKS', params={
                'pub': 'nwt',
                'booknum': entry.book_num,
                'track': entry.chapter_num,
                'output': 'json',
                'fileformat': 'MP3',
                'alllangs': 0,
                'langwritten': 'E',
                'txtCMSLang': 'E',
            })
            resp.raise_for_status()
        except requests.RequestException:
            return
        audio_data = resp.json()
        file_data = audio_data['files']['E']['MP3'][0]
        entry.audio_file_link = file_data['file']['url']
        entry.audio_file_duration = int(file_data['duration'])
        entry.audio_file_mimetype = file_data['mimetype']
        entry.save()


    def __str__(self):
        return f'DailyTextEntry[{self.day}, {self.name}]'
