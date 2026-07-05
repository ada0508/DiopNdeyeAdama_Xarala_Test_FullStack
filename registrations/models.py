from django.db import models

class Registration(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_whatsapp = models.CharField(max_length=20, unique=True)
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)