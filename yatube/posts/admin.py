from django.contrib import admin

from .models import Post, Group


class Postadmin(admin.ModelAdmin):
    list_display = ("pk", "text", "pub_date", "author")
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"


class Groupadmin(admin.ModelAdmin):
    list_display = ("pk", "title", "slug", "description")
    search_fields = ("title",)
    list_filter = ("id",)
    empty_value_display = "-пусто-"


admin.site.register(Post, Postadmin)
admin.site.register(Group, Groupadmin)
