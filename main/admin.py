# main/admin.py

from django.contrib import admin
from .models import UserPrompt, ChatMessage

@admin.register(UserPrompt)
class UserPromptAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'count')
    list_filter = ('date', 'user')
    search_fields = ('user__username',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'sender', 'timestamp', 'short_message')
    list_filter = ('sender', 'timestamp', 'user')
    search_fields = ('user__username', 'message')

    def short_message(self, obj):
        return obj.message[:50] + ("..." if len(obj.message) > 50 else "")
    short_message.short_description = 'Message'
