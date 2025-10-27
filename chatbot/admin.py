"""
Admin configuration for Chatbot
"""
from django.contrib import admin
from .models import ChatMessage, AIAssistant


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'timestamp', 'message_type')
    list_filter = ('message_type', 'timestamp')
    search_fields = ('user__username', 'message', 'response')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(AIAssistant)
class AIAssistantAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')