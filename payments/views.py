import logging
from decimal import Decimal
from django.db import transaction, IntegrityError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Order, PaymentEvent
from .utils import verify_signature

logger = logging.getLogger(__name__)

@api_view(['POST'])
def payment_webhook(request):
    data = request.data

    signature = data.get('signature', '')
    payload = f"{data.get('transaction_id')}{data.get('order_id')}{data.get('amount')}".encode()
    if not verify_signature(payload, signature):
        return Response({'error': 'Signature invalide'}, status=403)

    try:
        order = Order.objects.get(id=data.get('order_id'))
    except Order.DoesNotExist:
        return Response({'error': 'Commande inconnue'}, status=200)

    try:
        with transaction.atomic():
            event = PaymentEvent.objects.create(
                transaction_id=data.get('transaction_id'),
                order=order,
                status=data.get('status'),
                amount=Decimal(str(data.get('amount'))),
            )

            if event.amount != order.amount:
                logger.warning(f"ANOMALIE montant: webhook={event.amount}, commande={order.amount}, tx={event.transaction_id}")
                return Response({'message': 'Montant incohérent, anomalie tracée'}, status=200)

        
            if data.get('status') == 'success':
                order.status = 'paid'
                order.save()
                logger.info(f"LIVRAISON: accès au cours accordé pour la commande {order.id}")

    except IntegrityError:
        
        return Response({'message': 'Déjà traité'}, status=200)

    return Response({'message': 'OK'}, status=200)