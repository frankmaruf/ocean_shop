import graphene
from graphene_django import DjangoObjectType
from inventory.models import Product
from django.contrib.auth.models import User
from graphene import relay, ObjectType, String, ID
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.debug import DjangoDebug

class ProductType(DjangoObjectType):
    filter_fields = {
            'description': ['exact', 'icontains', 'istartswith'],
            'name': ['exact'],
            'categories__name': ['exact'],
        }
    interfaces = (relay.Node, )
    class Meta:
        model = Product
        fields = "__all__"
        interfaces = (relay.Node,)
        
class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=True)
        user_id = graphene.ID(required=False)

    post = graphene.Field(ProductType)

    def mutate(self, info, name, description, user_id):
        """
        The mutate function is the function that will be called when a client
        makes a request to this mutation. It takes in four arguments:
        self, info, title and content. The first two are required by all mutations;
        the last two are the arguments we defined in our CreatePostInput class.

        :param self: Access the object's attributes and methods
        :param info: Access the context of the request
        :param title: Create a new post with the title provided
        :param content: Pass the content of the post
        :param author_id: Get the author object from the database
        :return: A createpost object
        """
        author = User.objects.get(pk=user_id)
        product = Product(name=name, description=description, author=author)
        product.save()
        return CreateProduct(product=product)


# class UpdatePost(graphene.Mutation):
#     class Arguments:
#         id = graphene.ID(required=True)
#         title = graphene.String()
#         content = graphene.String()

#     post = graphene.Field(ProductType)

#     def mutate(self, info, id, title=None, content=None):
#         """
#         The mutate function is the function that will be called when a client
#         calls this mutation. It takes in four arguments: self, info, id and title.
#         The first two are required by all mutations and the last two are specific to this mutation.
#         The self argument refers to the class itself (UpdatePost) while info contains information about
#         the query context such as authentication credentials or access control lists.

#         :param self: Pass the instance of the class
#         :param info: Access the context of the request
#         :param id: Find the post we want to update
#         :param title: Update the title of a post
#         :param content: Update the content of a post
#         :return: An instance of the updatepost class, which is a subclass of mutation
#         """
#         try:
#             product = Product.objects.get(pk=id)
#         except Product.DoesNotExist:
#             raise Exception("Post not found")

#         if title is not None:
#             product.title = title
#         if content is not None:
#             product.content = content

#         product.save()
#         return UpdatePost(product=product)


# class DeletePost(graphene.Mutation):
#     class Arguments:
#         id = graphene.ID(required=True)

#     success = graphene.Boolean()

#     def mutate(self, info, id):
#         """
#         The mutate function is the function that will be called when a client
#         calls this mutation. It takes in four arguments: self, info, id. The first
#         argument is the object itself (the class instance). The second argument is
#         information about the query context and user making this request. We don't
#         need to use it here so we'll just pass it along as-is to our model method.
#         The third argument is an ID of a post we want to delete.

#         :param self: Represent the instance of the class
#         :param info: Access the context of the query
#         :param id: Find the post that is to be deleted
#         :return: A deletepost object, which is the return type of the mutation
#         """
#         try:
#             post = Product.objects.get(pk=id)
#         except Product.DoesNotExist:
#             raise Exception("Post not found")

#         product.delete()
#         return DeletePost(success=True)


class ProductConnection(relay.Connection):
    class Meta:
        node = ProductType



class Query(graphene.ObjectType):
    products = graphene.List(ProductType)
    debug = graphene.Field(DjangoDebug, name='_debug')
    patterns = relay.ConnectionField(ProductConnection)
    # authors = graphene.List(AuthorType)

    def resolve_products(self, info):
        
        """
        The resolve_posts function is a resolver. It’s responsible for retrieving the posts from the database and returning them to GraphQL.

        :param self: Refer to the current instance of a class
        :param info: Pass along the context of the query
        :return: All post objects from the database
        """
        
        return Product.objects.all()
        
            

    # def resolve_authors(self, info):
        """
        The resolve_authors function is a resolver. It’s responsible for retrieving the data that will be returned as part of an execution result.

        :param self: Pass the instance of the object to be used
        :param info: Pass information about the query to the resolver
        :return: A list of all the authors in the database
        """
        # return Author.objects.all()


class Mutation(graphene.ObjectType):
    create_post = CreateProduct.Field()
    # update_post = UpdateProduct.Field()
    # delete_post = DeleteProduct.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)