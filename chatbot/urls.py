"""
Chatbot URLs Configuration
"""
from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('api/send/', views.api_chat, name='api_chat'),
    path('api/history/', views.api_chat_history, name='api_history'),
    path('api/clear/', views.api_clear_history, name='api_clear'),
]

