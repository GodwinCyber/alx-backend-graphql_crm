import graphene

class Query(graphene.ObjectType):
    '''Root GraphQL query type'''
    hello = graphene.String(default_value="Hello, GraphQL!")

# Define the schema with the Query type
schema =graphene.Schema(query=Query)
