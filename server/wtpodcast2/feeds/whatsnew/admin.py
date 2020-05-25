from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    fields = [
        'guid',
        'title',
        'link',
        'description',
        'pub_date',
        'mid',
        'audio_file_link',
        'audio_file_duration',
        'audio_file_mimetype',
    ]
    list_display = fields
