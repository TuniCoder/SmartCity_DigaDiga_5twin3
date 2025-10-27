import stripe
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Clé API Stripe pour les tests


# Configuration de l'API Stripe

class StripeService:
    """
    Service pour gérer les paiements via Stripe
    """
    
    @staticmethod
    def create_payment_intent(amount, currency="eur", description=None, metadata=None):
        """
        Crée une intention de paiement Stripe
        
        Args:
            amount (int): Montant en centimes (ex: 1000 pour 10€)
            currency (str): Devise (par défaut: eur)
            description (str): Description du paiement
            metadata (dict): Métadonnées supplémentaires
            
        Returns:
            dict: L'intention de paiement créée
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                description=description,
                metadata=metadata
            )
            return {
                "success": True,
                "client_secret": intent.client_secret,
                "id": intent.id
            }
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'intention de paiement: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def retrieve_payment_intent(payment_intent_id):
        """
        Récupère une intention de paiement
        
        Args:
            payment_intent_id (str): ID de l'intention de paiement
            
        Returns:
            dict: L'intention de paiement
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "success": True,
                "payment_intent": intent
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'intention de paiement: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def create_checkout_session(price_id, success_url, cancel_url, metadata=None):
        """
        Crée une session de paiement Stripe Checkout
        
        Args:
            price_id (str): ID du prix Stripe
            success_url (str): URL de redirection en cas de succès
            cancel_url (str): URL de redirection en cas d'annulation
            metadata (dict): Métadonnées supplémentaires
            
        Returns:
            dict: La session de paiement créée
        """
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata
            )
            return {
                "success": True,
                "session_id": session.id,
                "url": session.url
            }
        except Exception as e:
            logger.error(f"Erreur lors de la création de la session de paiement: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def create_payment_link(amount, currency="eur", description=None):
        """
        Crée un lien de paiement Stripe
        
        Args:
            amount (int): Montant en centimes (ex: 1000 pour 10€)
            currency (str): Devise (par défaut: eur)
            description (str): Description du paiement
            
        Returns:
            dict: Le lien de paiement créé
        """
        try:
            # Créer un produit
            product = stripe.Product.create(
                name=description or "Paiement SmartCity",
                description=description or "Paiement pour services SmartCity"
            )
            
            # Créer un prix pour ce produit
            price = stripe.Price.create(
                product=product.id,
                unit_amount=amount,
                currency=currency
            )
            
            # Créer un lien de paiement
            payment_link = stripe.PaymentLink.create(
                line_items=[
                    {
                        "price": price.id,
                        "quantity": 1
                    }
                ]
            )
            
            return {
                "success": True,
                "payment_link": payment_link.url
            }
        except Exception as e:
            logger.error(f"Erreur lors de la création du lien de paiement: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }