from django.shortcuts import render
from rest_framework import mixins, generics
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib import messages
from rest_framework.pagination import PageNumberPagination
from inventory import models
from inventory import serializers
from django.shortcuts import get_object_or_404, get_list_or_404
from django.db.models import F
from .schema import product_list_doc

class Pagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        current_page_number = self.page.number

        last_page_number = self.page.paginator.num_pages
        max_pages = 10
        start_page = max(current_page_number - int(max_pages / 2), 1)
        end_page = start_page + max_pages

        if end_page > last_page_number:
            end_page = last_page_number + 1
            start_page = max(end_page - max_pages, 1)

        paginator_list = list(range(start_page, end_page))
        next_page_number = self.page.next_page_number() if self.page.has_next() else None
        previous_page_number = self.page.previous_page_number() if self.page.has_previous() else None

        return Response({
            'page_size': self.page_size,
            'paginator_list': paginator_list,
            'total_objects': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page_number': self.page.number,
            'next': next_page_number,
            'previous': previous_page_number,
            'last_page_number': last_page_number,
            'next_link': self.get_next_link(),
            'previous_link': self.get_previous_link(),
            'results': data,
        })


class APIColorsListView(generics.ListAPIView):
    queryset = models.Color.objects.filter(is_active=True, deleted=False).all()
    serializer_class = serializers.ColorSerializer
    pagination_class = Pagination



class APICategoryListView(generics.ListAPIView):
    queryset = models.Category.objects.filter(is_active=True, deleted=False).all()
    serializer_class = serializers.CategorySerializer
    pagination_class = Pagination


class APICategoryDetailView(APIView):
    pagination_class = Pagination
    def get_object(self, slug):
        try:
            return models.Category.objects.filter(is_active=True, deleted=False).get(slug=slug)
        except models.Category.DoesNotExist:
            raise Http404

    def get(self, request, slug, format=None):
        category = self.get_object(slug)
        serializer = serializers.CategorySerializer(category, context={'request': request})
        return serializer.data


class APICategoryProductsListView(APIView):
    pagination_class = Pagination
    def get_object(self, slug):
        try:
            return models.Category.objects.filter(is_active=True, deleted=False).get(slug=slug)
        except models.Category.DoesNotExist:
            raise Http404

    def get(self, request, slug, format=None):
        category = self.get_object(slug)
        products = models.Product.objects.filter(productcategories__category=category)
        paginator = self.pagination_class()
        paginated_products = paginator.paginate_queryset(products, request)
        serializer = serializers.ProductsSerializer(paginated_products, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class AttributeValueListView(generics.ListAPIView):
    queryset         = models.AttributeValues.objects.filter(is_active=True, deleted=False).all()
    serializer_class = serializers.AttributeValuesSerializer
    pagination_class = Pagination


class AttributeListView(generics.ListAPIView):
    queryset         = models.Attribute.objects.filter(is_active=True, deleted=False).all()
    serializer_class = serializers.AttributeSerializer
    pagination_class = Pagination


class ProductViewSet(ViewSet):
    lookup_field = 'slug'
    queryset = models.Product.objects.filter(is_active=True, deleted=False)

    @product_list_doc
    def list(self, request):
        category = request.query_params.get('category')
        if category:
            self.queryset = self.queryset.filter(categories=category)

        name = request.query_params.get('name')
        if name:
            self.queryset = self.queryset.filter(name__icontains=name)

        queryset = self.queryset.order_by(F('id'))
        pagination = Pagination()
        paginated_queryset = pagination.paginate_queryset(queryset, request)
        serializer = serializers.ProductsSerializer(paginated_queryset, many=True, context={'request': request})
        return pagination.get_paginated_response(serializer.data)

    def retrieve(self, request, slug=None):
        queryset = self.queryset
        product = get_object_or_404(queryset, slug=slug)
        serializer = serializers.ProductsDetailsSerializer(product, context={'request': request})
        return Response(serializer.data)