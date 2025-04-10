import graphene
import orders.schema , products.schema ,authentification.schema,   customers.schema ,addresses.schema   , notification.schema , stock.schema , categories.schema



class Query(
      orders.schema.Query,
      products.schema.Query,
      customers.schema.Query,
      addresses.schema.Query,
      authentification.schema.Query,
      notification.schema.Query,
      stock.schema.StockQuery,
      categories.schema.Query,

      

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


     graphene.ObjectType):
    
    
    pass
    



schema = graphene.Schema(query=Query ,  mutation=Mutation)
