from django.contrib import admin
from chat.models import ChatSession

# Register your models here.

class ChatSessionAdmin(admin.ModelAdmin):
    search_fields = ("id", "user_id", "start_time", "end_time")
    list_display = ["id", "user_id", "start_time", "end_time"]

admin.site.register(ChatSession, ChatSessionAdmin)