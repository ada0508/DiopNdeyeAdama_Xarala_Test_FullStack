from django.test import TestCase
from django.core.cache import cache
from .models import Registration


class RegistrationTests(TestCase):

    def setUp(self):
        cache.clear()
        self.data = {
            'name': 'Aminata Fall',
            'email': 'aminata@gmail.com',
            'phone_whatsapp': '+221771234567',
            'city': 'Thies',
        }

    def test_doublon(self):
        """La meme personne inscrite 2 fois → 1 seule inscription."""
        r1 = self.client.post('/registrations', self.data, content_type='application/json')
        self.assertEqual(r1.status_code, 201)

        r2 = self.client.post('/registrations', self.data, content_type='application/json')
        self.assertEqual(r2.status_code, 200)

        self.assertEqual(Registration.objects.count(), 1)

    def test_pic_de_requetes(self):
        """Au-dela de 10 requetes/minute → 429 (videur)."""
        derniere = None
        for i in range(11):
            data = dict(self.data, email=f"user{i}@gmail.com", phone_whatsapp=f"+2217712345{i:02d}")
            derniere = self.client.post('/registrations', data, content_type='application/json')
        self.assertEqual(derniere.status_code, 429)



    def test_telephone_invalide(self):
        """Un numero sans format international → 400, rien enregistre."""
        data = dict(self.data, phone_whatsapp='771234567') 
        response = self.client.post('/registrations', data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Registration.objects.count(), 0)