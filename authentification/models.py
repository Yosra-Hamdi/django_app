from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)  # Assure l'unicité de l'email
    phone = models.CharField(max_length=15, blank=True, null=True)
    store_name = models.CharField(max_length=100, blank=True, null=True)
    reset_code = models.CharField(max_length=6, null=True, blank=True)

    USERNAME_FIELD = "email"  # Utilisation de l'email comme identifiant principal
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def __str__(self):
        return self.email  # Afficher l'email comme nom de l'utilisateur
