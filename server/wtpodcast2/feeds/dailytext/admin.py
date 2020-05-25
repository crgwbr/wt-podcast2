from django.contrib import admin
from .models import DailyTextEntry


@admin.register(DailyTextEntry)
class DailyTextEntryAdmin(admin.ModelAdmin):
    fields = [
        'day',
        'content',
        'name',
        'book_num',
        'chapter_num',
        'verse_num',
        'audio_file_link',
        'audio_file_duration',
        'audio_file_mimetype',
        'imported',
    ]
    readonly_fields = [
        'imported',
    ]
    list_display = [
        'day',
        'name',
        'audio_file_link',
        'imported',
    ]
