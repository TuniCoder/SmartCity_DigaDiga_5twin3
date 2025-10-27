from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse
import json
import stripe

from .stripe_service import StripeService, STRIPE_API_KEY

def payment_page(request):
    """
    Page de paiement avec intégration Stripe
    """
    context = {
        'stripe_public_key': STRIPE_API_KEY,
    }
    return render(request, 'payment_service/payment.html', context)

def create_payment_intent(request):
    """
    Crée une intention de paiement Stripe
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = data.get('amount')
            description = data.get('description', 'Paiement SmartCity')
            
            # Créer l'intention de paiement
            result = StripeService.create_payment_intent(
                amount=amount,
                description=description,
                metadata={'user_id': request.user.id if request.user.is_authenticated else None}
            )
            
            if result['success']:
                return JsonResponse(result)
            else:
                return JsonResponse({'error': result['error']}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

def payment_success(request):
    """
    Page de succès après paiement
    """
    return render(request, 'payment_service/success.html')

def payment_cancel(request):
    """
    Page d'annulation de paiement
    """
    return render(request, 'payment_service/cancel.html')

@csrf_exempt
def stripe_webhook(request):
    """
    Webhook pour recevoir les événements Stripe
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, 'whsec_...'  # Remplacer par votre clé secrète de webhook
        )
        
        # Gérer les différents types d'événements
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            # Traiter le paiement réussi
            # Mettre à jour la base de données, envoyer un email, etc.
            print(f"Paiement réussi: {payment_intent['id']}")
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            # Traiter l'échec de paiement
            print(f"Paiement échoué: {payment_intent['id']}")
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def create_checkout_session(request):
    """
    Crée une session de paiement Stripe Checkout
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = data.get('amount')
            description = data.get('description', 'Paiement SmartCity')
            
            # Créer un produit et un prix pour la session
            product = stripe.Product.create(
                name=description,
                description=description
            )
            
            price = stripe.Price.create(
                product=product.id,
                unit_amount=amount,
                currency='eur'
            )
            
            # URL de succès et d'annulation
            success_url = request.build_absolute_uri(reverse('payment_success'))
            cancel_url = request.build_absolute_uri(reverse('payment_cancel'))
            
            # Créer la session de paiement
            result = StripeService.create_checkout_session(
                price_id=price.id,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={'user_id': request.user.id if request.user.is_authenticated else None}
            )
            
            if result['success']:
                return JsonResponse({'id': result['session_id'], 'url': result['url']})
            else:
                return JsonResponse({'error': result['error']}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

def create_payment_link(request):
    """
    Crée un lien de paiement Stripe
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = data.get('amount')
            description = data.get('description', 'Paiement SmartCity')
            
            # Créer le lien de paiement
            result = StripeService.create_payment_link(
                amount=amount,
                description=description
            )
            
            if result['success']:
                return JsonResponse({'payment_link': result['payment_link']})
            else:
                return JsonResponse({'error': result['error']}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)