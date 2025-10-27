"""
Chatbot Views for AI Assistant
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import logging
from openai import OpenAI

from .models import ChatMessage, AIAssistant

logger = logging.getLogger(__name__)


@login_required
def chat_view(request):
    """Page de chat avec l'assistant IA"""
    try:
        # Récupérer l'historique des messages de l'utilisateur
        chat_messages = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')[:20]
        
        # Récupérer ou créer l'assistant IA
        assistant, created = AIAssistant.objects.get_or_create(
            is_active=True,
            defaults={
                'name': 'Assistant SmartCity',
                'system_prompt': 'Tu es un assistant intelligent spécialisé dans la gestion de ville intelligente (SmartCity). Tu peux aider avec la gestion de véhicules, la mobilité urbaine, les transports, et toutes questions liées à la ville intelligente. Réponds en français de manière claire et professionnelle.'
            }
        )
        
        context = {
            'page_title': 'Assistant IA - SmartCity',
            'chat_messages': chat_messages,
            'assistant': assistant,
        }
        return render(request, 'chatbot/chat.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans chat_view: {e}")
        return render(request, 'chatbot/chat.html', {
            'page_title': 'Assistant IA - SmartCity',
            'chat_messages': [],
            'assistant': None,
        })


@login_required
@require_http_methods(["POST"])
def api_chat(request):
    """API pour chatter avec l'assistant IA"""
    try:
        # Vérifier que la clé API est configurée
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            logger.error("OPENAI_API_KEY n'est pas configurée dans les paramètres")
            return JsonResponse({
                'status': 'error',
                'message': 'La clé API OpenAI n\'est pas configurée. Veuillez configurer OPENAI_API_KEY dans votre fichier .env'
            }, status=500)
        
        # Initialiser le client OpenAI
        client = OpenAI(api_key=api_key)
        
        # Récupérer le message de l'utilisateur
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        message_type = data.get('type', 'question')
        
        if not user_message:
            return JsonResponse({
                'status': 'error',
                'message': 'Le message ne peut pas être vide'
            }, status=400)
        
        # Récupérer l'assistant IA
        try:
            assistant = AIAssistant.objects.get(is_active=True)
            system_prompt = assistant.system_prompt
        except AIAssistant.DoesNotExist:
            system_prompt = "Tu es un assistant intelligent spécialisé dans la gestion de ville intelligente (SmartCity). Réponds en français de manière claire et professionnelle."
        
        # Récupérer l'historique récent pour le contexte
        recent_messages = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')[:5]
        
        # Construire le contexte de conversation
        messages = [{"role": "system", "content": system_prompt}]
        
        # Ajouter l'historique de conversation (ordre inversé pour avoir les plus récents en dernier)
        for msg in reversed(recent_messages):
            messages.append({"role": "user", "content": msg.message})
            messages.append({"role": "assistant", "content": msg.response})
        
        # Ajouter le message actuel
        messages.append({"role": "user", "content": user_message})
        
        # Obtenir le modèle depuis les paramètres
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-4')
        
        # Appel à l'API OpenAI
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Sauvegarder la conversation
            chat_message = ChatMessage.objects.create(
                user=request.user,
                message=user_message,
                response=ai_response,
                message_type=message_type
            )
            
            return JsonResponse({
                'status': 'success',
                'response': ai_response,
                'message_id': chat_message.id,
                'timestamp': chat_message.timestamp.isoformat()
            })
            
        except Exception as api_error:
            # Gestion spécifique des erreurs OpenAI
            error_message = str(api_error)
            if 'insufficient_quota' in error_message or 'rate_limit' in error_message:
                user_friendly_message = "Limite de quota atteinte. Veuillez réessayer plus tard."
            elif 'invalid_api_key' in error_message or 'authentication' in error_message:
                user_friendly_message = "Erreur d'authentification. Vérifiez votre clé API."
            elif 'model' in error_message and 'not found' in error_message:
                user_friendly_message = f"Le modèle {model} n'est pas disponible. Veuillez vérifier votre configuration."
            else:
                user_friendly_message = f"Erreur lors de la communication avec l'API: {error_message}"
            
            logger.error(f"Erreur OpenAI API: {error_message}")
            return JsonResponse({
                'status': 'error',
                'message': user_friendly_message
            }, status=500)
        
    except Exception as e:
        logger.error(f"Erreur dans api_chat: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur lors de la communication avec l\'IA: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_chat_history(request):
    """API pour récupérer l'historique des conversations"""
    try:
        messages = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')[:50]
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'message': msg.message,
                'response': msg.response,
                'timestamp': msg.timestamp.isoformat(),
                'type': msg.message_type
            })
        
        return JsonResponse({
            'status': 'success',
            'messages': messages_data
        })
        
    except Exception as e:
        logger.error(f"Erreur dans api_chat_history: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur lors de la récupération de l\'historique: {str(e)}'
        })


@login_required
@require_http_methods(["DELETE"])
def api_clear_history(request):
    """API pour effacer l'historique des conversations"""
    try:
        ChatMessage.objects.filter(user=request.user).delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Historique effacé avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur dans api_clear_history: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur lors de l\'effacement de l\'historique: {str(e)}'
        })