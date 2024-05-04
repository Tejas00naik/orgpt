from django.contrib import admin
from chat.models import ChatSession

# Register your models here.

class ChatSessionAdmin(admin.ModelAdmin):
    search_fields = ("id", "user_id", "start_time", "end_time", "session_data_url")
    list_display = ["id", "user_id", "start_time", "end_time", "session_data_url"]

admin.site.register(ChatSession, ChatSessionAdmin)