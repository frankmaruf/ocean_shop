from rest_framework import serializers
from inventory import models

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Color
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = '__all__'



class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = ('id', 'name','slug')


class ProductRelatedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductRelatedImage
        fields = ('product_image','position',)


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Label
        fields = ('label_image','label_text')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.label_image:
            representation.pop('label_text')
        elif instance.label_text:
            representation.pop('label_image')
        return representation


class OfferTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OfferType
        fields = ('type','logo','banner',)


class ProductsSerializer(serializers.ModelSerializer):
    product_related_images = ProductRelatedImageSerializer(many=True)

    class Meta:
        model = models.Product
        fields = '__all__'


class ProductOfferSerializer(serializers.ModelSerializer):
    is_running = serializers.BooleanField(read_only=True)
    offer_type = serializers.SerializerMethodField()
    current_offer_price = serializers.DecimalField(decimal_places=2, max_digits=10, read_only=True)
    next_upcoming_offer_datetime = serializers.DateTimeField(read_only=True)

    class Meta:
        model = models.ProductOffer
        fields = ('current_offer_price','offer_type','is_running','next_upcoming_offer_datetime')

    def get_offer_type(self, obj):
        if hasattr(obj,"offer_type"):
            request = self.context['request']
            serializer = OfferTypeSerializer(obj.offer_type, context={'request': request})
            return serializer.data
        else:
            return None



class ProductSKUSerializer(serializers.ModelSerializer):
    product_sku_offers = ProductOfferSerializer()
    class Meta:
        model = models.ProductSKU
        fields = '__all__'



class ProductSEOSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductSEO
        fields = ('meta_title','meta_description','meta_keywords')


class ProductsDetailsSerializer(serializers.ModelSerializer):
    product_related_images = ProductRelatedImageSerializer( many=True)
    sku_product = serializers.SerializerMethodField()
    product_seo = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    product_offers = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    filters = serializers.SerializerMethodField()

    def get_sku_product(self, obj):
        if hasattr(obj,"product_variations"):
            request = self.context['request']
            serializer = ProductSKUSerializer(obj.product_variations, many=True, context={'request': request})
            return serializer.data
        else:
            return None

    def get_product_seo(self, obj):
        if hasattr(obj,"product_seo"):
            serializer = ProductSEOSerializer(obj.product_variations)
            return serializer.data
        else:
            return None

    def get_product_offers(self, obj):
        if obj.product_offers.exists():
            request = self.context['request']
            offer = obj.product_offers.first()
            object_of_offer = models.ProductOffer.objects.filter(id=offer.running_id).first()
            serializer = ProductOfferSerializer(object_of_offer, context={'request': request})
            return serializer.data
        return None

    def get_attributes(self,obj):
        product_attributes = models.ProductAttributeValues.objects.filter(product=obj).values_list('attribute_value__attribute', flat=True).distinct()
        attributes_data = []
        for product_attribute in product_attributes:
            attribute_ = models.Attribute.objects.filter(id=product_attribute).first()
            attribute_values = models.ProductAttributeValues.objects.filter(product=obj,attribute_value__attribute_id=product_attribute)
            attribute_data   = {
                'attribute_id'    : attribute_.id,
                'attribute_name'  : attribute_.attribute_name,
                'attribute_values': [
                    {
                        'attribute_values_id': attribute_value.attribute_value.id,
                        'attribute_values_name': attribute_value.attribute_value.attribute_values_name,
                        'attribute_values_position': attribute_value.position,
                    }
                    for attribute_value in attribute_values
                ]
            }
            attributes_data.append(attribute_data)
        return attributes_data

    def get_filters(self,obj):
        product_filters = models.ProductFilter.objects.filter(product=obj).values_list('filter__filter_group', flat=True).distinct()
        filters_data = []
        for product_filter in product_filters:
            filter_group_ = models.FilterGroup.objects.filter(id=product_filter).first()
            filters =  models.ProductFilter.objects.filter(product=obj,filter__filter_group=product_filter)
            filter_group = {
                'filter_id'    : filter_group_.id,
                'filter_group'  : filter_group_.name,
                'filters': [
                    {
                        'filter_id': filter.filter.id,
                        'filter_name': filter.filter.name,
                        'filter_position': filter.position,
                    }
                    for filter in filters
                ]
            }
            filters_data.append(filter_group)
        return filters_data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if 'tags' in representation and (not instance.tags.exists()):
            representation.pop('tags')
        if 'product_related_images' in representation and (not instance.product_related_images.exists()):
            representation.pop('product_related_images')
        if 'sku_product' in representation and (not self.get_sku_product(instance)):
            representation.pop('sku_product')
        if 'product_seo' in representation and (not self.get_product_seo(instance)):
            representation.pop('product_seo')
        if 'attributes' in representation and len(self.get_attributes(instance))==0:
            representation.pop('attributes')
        if 'filters' in representation and len(self.get_filters(instance))==0:
            representation.pop('filters')
        return representation

    class Meta:
        model = models.Product
        exclude = ['categories','deleted_by','created_by','updated_by','created_at','updated_at','deleted_at',"is_active","deleted"]


class AttributeValuesSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute_value.attribute.attribute_name')


    class Meta:
        model = models.ProductAttributeValues
        fields = '__all__'

class AttributeSerializer(serializers.ModelSerializer):
    attribute_values = serializers.SerializerMethodField()

    class Meta:
        model = models.Attribute
        fields= '__all__'

    def get_attribute_values(self,obj):
        attribute_values = models.AttributeValues.objects.filter(attribute_id = obj.id)
        serializer = AttributeValuesSerializer(attribute_values,many=True)
        return serializer.data



class AttributeValuesSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AttributeValues
        fields = '__all__'