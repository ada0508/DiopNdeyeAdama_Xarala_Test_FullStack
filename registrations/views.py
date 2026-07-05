import re
import logging
import requests
from django.db import IntegrityError, transaction
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from .models import Registration

logger = logging.getLogger(__name__)

WEBHOOK_SORTANT_URL = "https://automation.example.com/webhook"  

def envoyer_webhook_sortant(registration):
    """Previent le systeme d'automatisation, avec 3 essais en cas d'echec."""
    payload = {
        'name': registration.name,
        'email': registration.email,
        'phone_whatsapp': registration.phone_whatsapp,
        'city': registration.city,
    }
    for essai in range(3):
        try:
            r = requests.post(WEBHOOK_SORTANT_URL, json=payload, timeout=5)
            if r.status_code < 300:
                logger.info(f"Webhook sortant OK pour {registration.email}")
                return True
        except requests.RequestException:
            pass
        logger.warning(f"Webhook sortant echec (essai {essai + 1}/3) pour {registration.email}")
    return False


@api_view(['POST'])
@throttle_classes([AnonRateThrottle])
def register(request):
    data = request.data

    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    phone = (data.get('phone_whatsapp') or '').strip().replace(' ', '')
    city = (data.get('city') or '').strip()
    if not all([name, email, phone, city]):
        return Response({'error': 'Tous les champs sont requis'}, status=400)

    if not re.match(r'^\+\d{8,15}$', phone):
        return Response({'error': 'Telephone invalide, format attendu: +221771234567'}, status=400)

    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return Response({'error': 'Email invalide'}, status=400)

    try:
        with transaction.atomic():
            registration = Registration.objects.create(
                name=name, email=email, phone_whatsapp=phone, city=city
            )
    except IntegrityError:
        return Response({'message': 'Vous etes deja inscrit(e)'}, status=200)

    envoyer_webhook_sortant(registration)

    return Response({'message': 'Inscription reussie'}, status=201)