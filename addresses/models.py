from django.db import models

class Address(models.Model):
    COUNTRY_CHOICES = [
        ("Tunisie", "Tunisie"),
        ("France", "France"),
        ("Allemagne", "Allemagne"),
        ("Italie", "Italie"),
        ("Espagne", "Espagne"),
        ("États-Unis", "États-Unis"),
        ("Canada", "Canada"),
        ("Royaume-Uni", "Royaume-Uni"),
    ]

    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(
        max_length=100,
        choices=COUNTRY_CHOICES,
        default="Tunisie"
    )

    def __str__(self):
        return f"{self.street}, {self.city}, {self.postal_code}, {self.country}"
