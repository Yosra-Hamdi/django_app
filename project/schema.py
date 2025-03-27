import graphene
import orders.schema , products.schema ,authentification.schema,   customers.schema ,addresses.schema 



class Query(
      orders.schema.Query,
      products.schema.Query,
      customers.schema.Query,
      addresses.schema.Query,
      authentification.schema.Query,
      

      graphene.ObjectType):
        pass
class Mutation(
     addresses.schema.Mutation,
     products.schema.Mutation,
     orders.schema.Mutation,
     authentification.schema.Mutation,
     graphene.ObjectType):
    
    
    pass
    



schema = graphene.Schema(query=Query ,  mutation=Mutation)
