import hmac
import hashlib
from django.test import TestCase
from django.conf import settings
from .models import Order, PaymentEvent


def make_signature(transaction_id, order_id, amount):
    """Fabrique une signature valide, comme Wave le ferait."""
    message = f"{transaction_id}{order_id}{amount}".encode()
    return hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        message,
        hashlib.sha256
    ).hexdigest()


class WebhookTests(TestCase):

    def setUp(self):
        # Cree une commande de test a 10000 F avant chaque test
        self.order = Order.objects.create(amount=10000)

    def test_replay_webhook(self):
        """Le meme webhook envoye 2 fois → 1 seul traitement."""
        data = {
            'transaction_id': 'TX001',
            'order_id': self.order.id,
            'status': 'success',
            'amount': 10000,
            'signature': make_signature('TX001', self.order.id, 10000),
        }
        response1 = self.client.post('/webhooks/payment', data, content_type='application/json')
        self.assertEqual(response1.status_code, 200)

        response2 = self.client.post('/webhooks/payment', data, content_type='application/json')
        self.assertEqual(response2.status_code, 200)

        # La preuve d'idempotence : UN seul evenement enregistre
        self.assertEqual(PaymentEvent.objects.count(), 1)

    def test_signature_invalide(self):
        """Un message avec une fausse signature doit etre rejete en 403."""
        data = {
            'transaction_id': 'TX999',
            'order_id': self.order.id,
            'status': 'success',
            'amount': 10000,
            'signature': 'fausse-signature',
        }
        response = self.client.post('/webhooks/payment', data, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        # Rejete AVANT le registre → aucun evenement ecrit
        self.assertEqual(PaymentEvent.objects.count(), 0)

    def test_montant_incoherent(self):
        """Montant du webhook different de la commande → pas de validation."""
        data = {
            'transaction_id': 'TX003',
            'order_id': self.order.id,
            'status': 'success',
            'amount': 5000,
            'signature': make_signature('TX003', self.order.id, 5000),
        }
        response = self.client.post('/webhooks/payment', data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # La commande ne doit PAS etre passee en "paid"
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'pending')