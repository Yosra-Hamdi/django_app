from decimal import Decimal
import graphene
from graphene_django import DjangoObjectType
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

class CreateLigneDevisInput(graphene.InputObjectType):
    id = graphene.ID()  # Rendu optionnel
    product_id = graphene.ID(required=True)
    quantite = graphene.Int(required=True)
    prix_unitaire_ht = graphene.Decimal()
    tva = graphene.Decimal()

class CreateDevisInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
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

        last_devis = Devis.objects.order_by('-id').first()
        ref_number = 1 if not last_devis else last_devis.id + 1
        reference = f"DEV-{datetime.now().year}-{ref_number:03d}"

        devis = Devis(
            customer_id=input['customer_id'],
            reference=reference,
            date_validite=datetime.strptime(input['date_validite'], "%Y-%m-%d").date(),
            remise=Decimal(str(input.get('remise', 0))),
            notes=input.get('notes', ''),
        )
        devis.save()

        for ligne_input in input['lignes']:
            ligne = LigneDevis(
                devis=devis,
                product_id=ligne_input['product_id'],
                quantite=ligne_input['quantite'],
                tva=Decimal(str(ligne_input.get('tva', 20.0))),
            )
            
            if 'prix_unitaire_ht' in ligne_input:
                ligne.prix_unitaire_ht = Decimal(str(ligne_input['prix_unitaire_ht']))
            
            ligne.save()

        return CreateDevis(devis=devis)

class UpdateLigneDevisInput(graphene.InputObjectType):
    id = graphene.ID()  # Rendu optionnel pour nouvelles lignes
    product_id = graphene.ID()
    quantite = graphene.Int()
    prix_unitaire_ht = graphene.Decimal()
    tva = graphene.Decimal()

class UpdateDevisInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    customer_id = graphene.ID()
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
        from datetime import datetime
        from decimal import Decimal
        
        try:
            devis = Devis.objects.get(pk=input['id'])
        except Devis.DoesNotExist:
            raise Exception("Devis non trouvé")

        if 'customer_id' in input:
            devis.customer_id = input['customer_id']
        if 'date_validite' in input:
            devis.date_validite = datetime.strptime(input['date_validite'], "%Y-%m-%d").date()
        if 'remise' in input:
            devis.remise = Decimal(str(input['remise']))
        if 'notes' in input:
            devis.notes = input['notes']
        if 'status' in input:
            devis.status = input['status']

        devis.save()

        if 'lignes' in input:
            for ligne_input in input['lignes']:
                if ligne_input.get('id'):
                    try:
                        ligne = LigneDevis.objects.get(pk=ligne_input['id'], devis=devis)
                        if 'product_id' in ligne_input:
                            ligne.product_id = ligne_input['product_id']
                        if 'quantite' in ligne_input:
                            ligne.quantite = ligne_input['quantite']
                        if 'tva' in ligne_input:
                            ligne.tva = Decimal(str(ligne_input['tva']))
                        if 'prix_unitaire_ht' in ligne_input:
                            ligne.prix_unitaire_ht = Decimal(str(ligne_input['prix_unitaire_ht']))
                        ligne.save()
                    except LigneDevis.DoesNotExist:
                        raise Exception(f"Ligne de devis {ligne_input['id']} non trouvée")
                else:
                    ligne = LigneDevis(
                        devis=devis,
                        product_id=ligne_input['product_id'],
                        quantite=ligne_input['quantite'],
                        tva=Decimal(str(ligne_input.get('tva', 20.0))),
                    )
                    if 'prix_unitaire_ht' in ligne_input:
                        ligne.prix_unitaire_ht = Decimal(str(ligne_input['prix_unitaire_ht']))
                    ligne.save()

        return UpdateDevis(devis=devis)

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
        product_id = graphene.ID(required=True)
        quantite = graphene.Int(required=True)
        prix_unitaire_ht = graphene.Decimal()
        tva = graphene.Decimal()

    ligne = graphene.Field(LigneDevisType)
    devis = graphene.Field(DevisType)

    def mutate(self, info, devis_id, product_id, quantite, prix_unitaire_ht=None, tva=None):
        try:
            devis = Devis.objects.get(pk=devis_id)
            ligne = LigneDevis(
                devis=devis,
                product_id=product_id,
                quantite=quantite,
                tva=Decimal(str(tva)) if tva else Decimal('20.0'),
            )
            
            if prix_unitaire_ht:
                ligne.prix_unitaire_ht = Decimal(str(prix_unitaire_ht))
            
            ligne.save()
            return AddLigneDevis(ligne=ligne, devis=devis)
        except Devis.DoesNotExist:
            raise Exception("Devis non trouvé")

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