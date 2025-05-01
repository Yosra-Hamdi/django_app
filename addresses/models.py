from django.db import models

class Address(models.Model):
    GOUVERNORAT_CHOICES = [
    ("Tunis", "Tunis"),
    ("Ariana", "Ariana"),
    ("Ben Arous", "Ben Arous"),
    ("Manouba", "Manouba"),
    ("Nabeul", "Nabeul"),
    ("Zaghouan", "Zaghouan"),
    ("Bizerte", "Bizerte"),
    ("Béja", "Béja"),
    ("Jendouba", "Jendouba"),
    ("Kef", "Kef"),
    ("Siliana", "Siliana"),
    ("Sousse", "Sousse"),
    ("Monastir", "Monastir"),
    ("Mahdia", "Mahdia"),
    ("Kairouan", "Kairouan"),
    ("Kasserine", "Kasserine"),
    ("Sidi Bouzid", "Sidi Bouzid"),
    ("Sfax", "Sfax"),
    ("Gabès", "Gabès"),
    ("Medenine", "Medenine"),
    ("Tataouine", "Tataouine"),
    ("Gafsa", "Gafsa"),
    ("Tozeur", "Tozeur"),
    ("Kebili", "Kebili"),
]


    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    governorate = models.CharField(
    max_length=100,
    choices=GOUVERNORAT_CHOICES,
    default="Tunis"
)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.postal_code}, {self.governorate}"
