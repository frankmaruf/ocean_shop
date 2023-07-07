from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from .serializers import ProductsSerializer, ProductsDetailsSerializer

product_list_doc = extend_schema(
    responses=ProductsSerializer(many=True),
    parameters=[
        OpenApiParameter(
            name="category",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Products list based on category"
        ),
        OpenApiParameter(
            name="name",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Products Name"
        ),
    ]
)
