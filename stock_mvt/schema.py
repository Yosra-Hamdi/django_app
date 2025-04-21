import graphene
from graphene_django import DjangoObjectType
from .models import StockMovement

class StockMovementType(DjangoObjectType):
    user_email = graphene.String()
    user_name = graphene.String()
    reason_display = graphene.String()  # Nouveau champ pour l'affichage du reason

    class Meta:
        model = StockMovement
        fields = "__all__"
    
    def resolve_reason(self, info):
        # Retourne la valeur brute stockée en base
        return self.reason
    
    def resolve_reason_display(self, info):
        # Retourne le label lisible correspondant à la valeur
        return self.get_reason_display()
    
    def resolve_user_email(self, info):
        return self.user.email if self.user else None
    
    def resolve_user_name(self, info):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username
        return None

class StockMovementReasonType(graphene.Enum):
    SOLD = 'SOLD'
    RETURN = 'RETURN'
    DAMAGED = 'DAMAGED'
    WITHDRAWAL = 'WITHDRAWAL'
    RESTOCK = 'RESTOCK'
    
    @property
    def description(self):
        # Map les valeurs aux labels Django
        return dict(StockMovement.REASONS).get(self.value, self.value)

class StockQuery(graphene.ObjectType):
    all_stock_movements = graphene.List(
        StockMovementType, 
        product_id=graphene.ID(required=True),
        description="Historique des mouvements de stock pour un produit"
    )

    def resolve_all_stock_movements(root, info, product_id):
        return StockMovement.objects.filter(
            stock__product__id=product_id
        ).select_related('user').order_by('-timestamp')

class CreateStockMovement(graphene.Mutation):
    class Arguments:
        stock_id = graphene.ID(required=True)
        quantity = graphene.Int(required=True)
        reason = graphene.Argument(StockMovementReasonType, required=True)
    
    movement = graphene.Field(StockMovementType)
    
    @classmethod
    def mutate(cls, root, info, stock_id, quantity, reason):
        user = info.context.user
        if not user or user.is_anonymous:
            raise Exception("Authentification requise")
        
        movement = StockMovement(
            stock_id=stock_id,
            quantity=quantity,
            reason=reason.value,  # Utilisation de .value pour la valeur brute
           
        )
        movement.user = user
        movement._current_user = user
        movement.save()
        
        return CreateStockMovement(movement=movement)

class StockMutation(graphene.ObjectType):
    create_stock_movement = CreateStockMovement.Field()

schema = graphene.Schema(query=StockQuery, mutation=StockMutation)