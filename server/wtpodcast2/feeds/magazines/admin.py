from django.contrib import admin
from .models import Issue, Article


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    fields = [
        'name',
        'pub',
        'pub_name',
        'issue_date',
        'formatted_issue_date',
        'cover_image',
        'imported',
    ]
    readonly_fields = [
        'name',
        'imported',
    ]
    list_display = [
        'name',
        'cover_image',
        'audio_file',
        'imported',
    ]



@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        'mid',
        'title',
        'issue',
        'track',
        'audio_file',
    ]
