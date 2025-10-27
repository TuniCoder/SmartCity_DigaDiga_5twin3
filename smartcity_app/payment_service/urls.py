from django.urls import path
from . import views

urlpatterns = [
    path('payment/', views.payment_page, name='payment_page'),
    path('create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('create-payment-link/', views.create_payment_link, name='create_payment_link'),
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]