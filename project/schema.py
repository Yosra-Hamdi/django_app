import graphene
import orders.schema  ,  customers.schema , stock.schema 
import products.schema , notification.schema , gallery.schema
import authentification.schema,addresses.schema , categories.schema
import stock_mvt.schema

class Query(
      orders.schema.Query,
      products.schema.Query,
      customers.schema.Query,
      addresses.schema.Query,
      authentification.schema.Query,
      notification.schema.Query,
      stock.schema.StockQuery,
      categories.schema.Query,
      gallery.schema.Query,
      stock_mvt.schema.StockQuery,
      

      

      graphene.ObjectType):
        pass
class Mutation(
     addresses.schema.Mutation,
     products.schema.Mutation,
     orders.schema.Mutation,
     authentification.schema.Mutation,
     notification.schema.Mutation,
     stock.schema.StockMutation,
     categories.schema.Mutation,
     gallery.schema.Mutation,
     stock_mvt.schema.StockMutation,
      customers.schema.Mutation,


     graphene.ObjectType):
    
    
    pass
    



schema = graphene.Schema(query=Query ,  mutation=Mutation)
