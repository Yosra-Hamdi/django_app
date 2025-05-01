# Méthodes de paiement
PAYMENT_METHOD_CHOICES = [
    ('CASH', 'Espèces '),
    ('CARD', 'Carte bancaire'),
]
# Statuts paiement
PAYMENT_STATUS_CHOICES = [
    ('PENDING', 'En attente'),
    ('PAID', 'Payée'),
    ('FAILED', 'Échoué'),
    ('REFUNDED', 'Remboursé'),
]