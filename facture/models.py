from django.db import models

from company.models import CompanyInfo
from orders.models import Order
from django.utils import timezone 

# Create your models here.
class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField(auto_now_add=True) ## Date d'émission de la facture
    due_date = models.DateField() ## Date d'échéance de la facture
   

    def generate_invoice_number(self):
        date_part = timezone.now().strftime('%Y%m')
        return f"FACT-{date_part}-{self.id:05d}"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
            super().save(update_fields=['invoice_number'])

    @property
    def company_info(self):
        """Retourne les infos de l'entreprise sous forme de dictionnaire"""
        company = CompanyInfo.objects.first()
        if not company:
            return {
                'name': '',
                'address': '',
                'phone': '',
                'email': '',
                'logo': ''
            }
        return {
            'name': company.name,
            'address': str(company.address) if company.address else '',
            'phone': company.phone,
            'email': company.email,
            'logo': company.logo.url if company.logo else ''
        }