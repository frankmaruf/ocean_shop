import graphene

import inventory.qlschema


class Query(inventory.qlschema.Query, graphene.ObjectType):
    # Combine the queries from different apps
    pass


class Mutation(inventory.qlschema.Mutation, graphene.ObjectType):
    # Combine the mutations from different apps
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)