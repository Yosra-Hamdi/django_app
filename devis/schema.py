from datetime import datetime
from decimal import Decimal
import graphene
from graphene_django import DjangoObjectType

from customers.models import Customer
from products.models import Product
from stock.models import Stock
from .models import Devis, LigneDevis

class LigneDevisType(DjangoObjectType):
    montant_ht = graphene.Float()
    montant_tva = graphene.Float()

    class Meta:
        model = LigneDevis
        fields = "__all__"

    def resolve_montant_ht(self, info):
        return float(Decimal(str(self.montant_ht)))


    def resolve_montant_tva(self, info):
        return float(Decimal(str(self.montant_tva)))
    
class DevisType(DjangoObjectType):
    total_ht = graphene.Float()
    total_tva = graphene.Float()
    total_ttc = graphene.Float()
    lignes = graphene.List(LigneDevisType)
    company_info = graphene.JSONString() 

    class Meta:
        model = Devis
        fields = "__all__"

    def resolve_total_ht(self, info):
        return float(self.total_ht)

    def resolve_total_tva(self, info):
        return float(self.total_tva)

    def resolve_total_ttc(self, info):
        return float(self.total_ttc)

    def resolve_lignes(self, info):
        return self.lignes.all()
    
    def resolve_company_info(self, info):
        return self.company_info

class CustomProductInput(graphene.InputObjectType):
    """Input pour les produits créés à la volée"""
    name = graphene.String(required=True)
    selling_price = graphene.Decimal(required=True)
    vat_rate = graphene.Decimal(default_value=Decimal('0.00'))
    unit = graphene.String(default_value="kg")


class TempCustomerInput(graphene.InputObjectType):
    last_name = graphene.String(required=True)
    first_name = graphene.String(required=True)
    phone = graphene.String(required=True)
    email = graphene.String()

#
class CreateLigneDevisInput(graphene.InputObjectType):
    product_id = graphene.ID(description="ID du produit existant (optionnel si custom_product)")
    custom_product = graphene.Field(CustomProductInput, description="Produit à créer (optionnel si product_id)")
    quantite = graphene.Int(required=True)
    prix_unitaire_ht = graphene.Decimal(description="Prix unitaire HT (écrase le prix du produit si spécifié)")
    tva = graphene.Decimal(description="Taux TVA (écrase celui du produit si spécifié)")

#
class CreateDevisInput(graphene.InputObjectType):
    customer_id = graphene.ID(description="ID d'un client existant (optionnel si temp_customer)")
    temp_customer = graphene.Field(TempCustomerInput, description="Infos client temporaire")
    date_validite = graphene.String(required=True)
    lignes = graphene.List(CreateLigneDevisInput, required=True)
    remise = graphene.Decimal()
    notes = graphene.String()


class CreateDevis(graphene.Mutation):
    class Arguments:
        input = CreateDevisInput(required=True)

    devis = graphene.Field(DevisType)

    def mutate(self, info, input):
        from datetime import datetime
        from django.db import transaction

        try:
            with transaction.atomic():
                # Création du client si nécessaire
                if input.get('temp_customer'):
                    customer_data = input['temp_customer']
                    customer = Customer.objects.create(
                        last_name=customer_data['last_name'],
                        first_name=customer_data['first_name'],
                        phone=customer_data['phone'],
                        email=customer_data.get('email', '')
                    )
                    customer_id = customer.id
                else:
                    customer_id = input['customer_id']
                        # Génération référence
                last_devis = Devis.objects.order_by('-id').first()
                ref_number = 1 if not last_devis else last_devis.id + 1
                reference = f"DEV-{datetime.now().year}-{ref_number:03d}"

                # Création devis
                devis = Devis.objects.create(
                    customer_id=customer_id,
                    reference=reference,
                    date_validite=datetime.strptime(input['date_validite'], "%Y-%m-%d").date(),
                    remise=Decimal(str(input.get('remise', 0))),
                    notes=input.get('notes', ''),
                )

                # Traitement des lignes
                for ligne_input in input['lignes']:
                    product_id = None
                    tva = Decimal(str(ligne_input.get('tva', 20.0)))
                    prix_unitaire = None

                    # Gestion produit personnalisé
                    if ligne_input.get('custom_product'):
                        custom = ligne_input['custom_product']
                        product = Product.objects.create(
                            name=custom['name'],
                            selling_price=Decimal(str(custom['selling_price'])),
                            vat_rate=tva,  # Utilise la TVA fournie ou 20% par défaut
                            unit=custom.get('unit', 'kg'),
                            purchase_price=0,
                            include_vat=False
                        )
                        Stock.objects.create(product=product, quantity=0)
                        product_id = product.id
                    else:
                        product_id = ligne_input['product_id']
                        if not product_id:
                            raise Exception("Product ID or custom product required")

                    # Création ligne
                    LigneDevis.objects.create(
                        devis=devis,
                        product_id=product_id,
                        quantite=ligne_input['quantite'],
                        tva=tva,
                        prix_unitaire_ht=Decimal(str(ligne_input['prix_unitaire_ht'])) if 'prix_unitaire_ht' in ligne_input else None
                    )

                return CreateDevis(devis=devis)

        except Exception as e:
            raise Exception(f"Erreur création devis: {str(e)}")      

            

class UpdateLigneDevisInput(graphene.InputObjectType):
    id = graphene.ID()  # Rendu optionnel pour nouvelles lignes
    product_id = graphene.ID()
    custom_product = graphene.Field(CustomProductInput)  # Ajoutez cette ligne
    quantite = graphene.Int()
    prix_unitaire_ht = graphene.Decimal()
    tva = graphene.Decimal()

class UpdateDevisInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    customer_id = graphene.ID(description="ID d'un client existant (optionnel si temp_customer)")
    temp_customer = graphene.Field(TempCustomerInput, description="Infos client temporaire")
    date_validite = graphene.String()
    lignes = graphene.List(UpdateLigneDevisInput)
    remise = graphene.Decimal()
    notes = graphene.String()
    status = graphene.String()

class UpdateDevis(graphene.Mutation):
    class Arguments:
        input = UpdateDevisInput(required=True)

    devis = graphene.Field(DevisType)

    def mutate(self, info, input):
        from django.db import transaction

        try:
            with transaction.atomic():
                devis = Devis.objects.select_for_update().get(pk=input['id'])
                
                # Gestion du client (nouveau ou existant)
                if input.get('temp_customer'):
                    customer_data = input['temp_customer']
                    customer = Customer.objects.create(
                        last_name=customer_data['last_name'],
                        first_name=customer_data['first_name'],
                        phone=customer_data['phone'],
                        email=customer_data.get('email', '')
                    )
                    devis.customer_id = customer.id
                    devis.save(update_fields=['customer_id'])
                elif 'customer_id' in input:
                    devis.customer_id = input['customer_id']
                    devis.save(update_fields=['customer_id'])

                # Mise à jour des autres champs de base
                update_fields = []
                if 'date_validite' in input:
                    devis.date_validite = datetime.strptime(input['date_validite'], "%Y-%m-%d").date()
                    update_fields.append('date_validite')
                if 'remise' in input:
                    devis.remise = Decimal(str(input['remise']))
                    update_fields.append('remise')
                if 'notes' in input:
                    devis.notes = input['notes']
                    update_fields.append('notes')
                if 'status' in input:
                    devis.status = input['status']
                    update_fields.append('status')
                
                if update_fields:
                    devis.save(update_fields=update_fields)

                # Gestion des lignes (reste inchangé)
                if 'lignes' in input:
                    kept_ids = [l['id'] for l in input['lignes'] if l.get('id')]
                    devis.lignes.exclude(id__in=kept_ids).delete()

                    for ligne_input in input['lignes']:
                        if ligne_input.get('id'):
                            ligne = LigneDevis.objects.get(
                                pk=ligne_input['id'],
                                devis=devis
                            )
                            if 'product_id' in ligne_input:
                                ligne.product_id = ligne_input['product_id']
                            if 'quantite' in ligne_input:
                                ligne.quantite = ligne_input['quantite']
                            if 'tva' in ligne_input:
                                ligne.tva = Decimal(str(ligne_input['tva']))
                            if 'prix_unitaire_ht' in ligne_input:
                                ligne.prix_unitaire_ht = Decimal(str(ligne_input['prix_unitaire_ht']))
                            ligne.save()
                        else:
                            if ligne_input.get('custom_product'):
                                custom = ligne_input['custom_product']
                                product = Product.objects.create(
                                    name=custom['name'],
                                    selling_price=Decimal(str(custom['selling_price'])),
                                    vat_rate=Decimal(str(custom.get('vat_rate', 20.0))),
                                    unit=custom.get('unit', 'kg'),
                                    purchase_price=0,
                                    include_vat=False
                                )
                                Stock.objects.create(product=product, quantity=0)
                                product_id = product.id
                            else:
                                product_id = ligne_input['product_id']
                            
                            LigneDevis.objects.create(
                                devis=devis,
                                product_id=product_id,
                                quantite=ligne_input['quantite'],
                                tva=Decimal(str(ligne_input.get('tva', 20.0))),
                                prix_unitaire_ht=Decimal(str(ligne_input.get('prix_unitaire_ht'))) if 'prix_unitaire_ht' in ligne_input else None
                            )

                return UpdateDevis(devis=devis)

        except Devis.DoesNotExist:
            raise Exception("Devis non trouvé")
        except Exception as e:
            raise Exception(f"Erreur mise à jour devis: {str(e)}")
class DeleteDevis(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id):
        try:
            devis = Devis.objects.get(pk=id)
            devis.delete()
            return DeleteDevis(success=True, message="Devis supprimé avec succès")
        except Devis.DoesNotExist:
            return DeleteDevis(success=False, message="Devis non trouvé")

class AddLigneDevis(graphene.Mutation):
    class Arguments:
        devis_id = graphene.ID(required=True)
        input = CreateLigneDevisInput(required=True)
       
    ligne = graphene.Field(LigneDevisType)
    

    def mutate(self, info, devis_id,input):
        
        devis = Devis.objects.get(id=devis_id)
           
        ligne = LigneDevis(
            devis=devis,
            product_id=input.get('product_id'),
            
            quantite=input['quantite'],
            prix_unitaire_ht=Decimal(str(input['prix_unitaire_ht'])),
            tva=Decimal(str(input['tva']))
        )
        ligne.save()
        return AddLigneDevis(ligne=ligne)

class UpdateLigneDevis(graphene.Mutation):
    class Arguments:
        ligne_id = graphene.ID(required=True)
        quantite = graphene.Int()
        prix_unitaire_ht = graphene.Decimal()
        tva = graphene.Decimal()

    ligne = graphene.Field(LigneDevisType)
    devis = graphene.Field(DevisType)

    def mutate(self, info, ligne_id, quantite=None, prix_unitaire_ht=None, tva=None):
        try:
            ligne = LigneDevis.objects.get(pk=ligne_id)
            if quantite is not None:
                ligne.quantite = quantite
            if prix_unitaire_ht is not None:
                ligne.prix_unitaire_ht = Decimal(str(prix_unitaire_ht))
            if tva is not None:
                ligne.tva = Decimal(str(tva))
            
            ligne.save()
            return UpdateLigneDevis(ligne=ligne, devis=ligne.devis)
        except LigneDevis.DoesNotExist:
            raise Exception("Ligne de devis non trouvée")

class RemoveLigneDevis(graphene.Mutation):
    class Arguments:
        ligne_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    devis = graphene.Field(DevisType)

    def mutate(self, info, ligne_id):
        try:
            ligne = LigneDevis.objects.get(pk=ligne_id)
            devis = ligne.devis
            ligne.delete()
            return RemoveLigneDevis(success=True, message="Ligne supprimée", devis=devis)
        except LigneDevis.DoesNotExist:
            return RemoveLigneDevis(success=False, message="Ligne non trouvée", devis=None)
class Query(graphene.ObjectType):
    all_devis = graphene.List(DevisType)
    devis_by_customer = graphene.List(DevisType, customer_id=graphene.ID(required=True))
    devis_by_status = graphene.List(DevisType, status=graphene.String())
    devis_by_id = graphene.Field(DevisType, id=graphene.ID(required=True))

    def resolve_all_devis(root, info):
        return Devis.objects.select_related('customer').prefetch_related('lignes').all()

    def resolve_devis_by_customer(root, info, customer_id):
        return Devis.objects.filter(customer_id=customer_id)

    def resolve_devis_by_status(root, info, status):
        return Devis.objects.filter(status=status)
        
    def resolve_devis_by_id(root, info, id):
        try:
            return Devis.objects.get(pk=id)
        except Devis.DoesNotExist:
            return None

class Mutation(graphene.ObjectType):
    create_devis = CreateDevis.Field()
    update_devis = UpdateDevis.Field()
    delete_devis = DeleteDevis.Field()
    add_ligne_devis = AddLigneDevis.Field()
    update_ligne_devis = UpdateLigneDevis.Field()
    remove_ligne_devis = RemoveLigneDevis.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)