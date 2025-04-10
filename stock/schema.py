import graphene
from graphene_django import DjangoObjectType
from .models import Stock
from products.models import Product

class StockType(DjangoObjectType):
    class Meta:
        model = Stock
        fields = "__all__"

class IncreaseStockInput(graphene.InputObjectType):
    product_id = graphene.ID(required=True, description="ID du produit")
    quantity = graphene.Int(required=True, description="Quantité à ajouter (négative pour retirer)")

class IncreaseStock(graphene.Mutation):
    class Arguments:
        input = IncreaseStockInput(required=True)

    stock = graphene.Field(StockType)
    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, input):
        try:
            product_id = input.product_id
            quantity = input.quantity

            # 1. Récupérer le produit et son stock
            product = Product.objects.get(id=product_id)
            stock = Stock.objects.get(product=product)

            # 2. Mettre à jour la quantité
            stock.quantity += quantity
            stock.save()

            return IncreaseStock(
                stock=stock,
                success=True,
                message=f"Stock mis à jour. Nouvelle quantité: {stock.quantity}"
            )

        except Product.DoesNotExist:
            return IncreaseStock(
                stock=None,
                success=False,
                message="Produit non trouvé"
            )
        except Stock.DoesNotExist:
            return IncreaseStock(
                stock=None,
                success=False,
                message="Stock non trouvé pour ce produit"
            )
        except Exception as e:
            return IncreaseStock(
                stock=None,
                success=False,
                message=f"Erreur: {str(e)}"
            )

class StockQuery(graphene.ObjectType):
    all_stocks = graphene.List(StockType)
    stock_by_product = graphene.Field(StockType, product_id=graphene.ID(required=True))

    def resolve_all_stocks(root, info):
        return Stock.objects.select_related('product').all()

    def resolve_stock_by_product(root, info, product_id):
        try:
            return Stock.objects.get(product_id=product_id)
        except Stock.DoesNotExist:
            return None

class StockMutation(graphene.ObjectType):
    increase_stock = IncreaseStock.Field()

# Schema final
schema = graphene.Schema(query=StockQuery, mutation=StockMutation)