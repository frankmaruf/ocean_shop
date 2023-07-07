from django.contrib import admin
from inventory import models
from django.contrib.auth.models import User

admin.site.register([
    models.Category,
    models.Brand,
    models.ProductCategories,
    models.ProductRelatedImage,
    models.Product,
    models.Color,
    models.ProductColor,
    models.Attribute,
    models.AttributeValues,
    models.ProductAttributeValues,
    models.ProductSKU,
    models.OfferType,
    models.LabelType,
    models.Label,
    models.ProductStockStatus,
    models.ProductOfferLog,
    models.Warehouse,
    models.StockEntryPurpose,
    models.ProductWarehouse,
    models.ProductOffer,
    models.ProductLabel,
    models.ProductPrice,
    models.ProductTags,
    models.Tag,
    models.ProductFilter,
    models.Filter,
    models.FilterGroup,
    ])

# class ProductWarehouseAdmin(admin.ModelAdmin):

#     def save_model(self, request, obj, form, change):
#         if not change:
#             event_type = "Product Warehouse Created From Admin"
#             quantity = obj.stock_quantity
#         else:
#             event_type = "Product Warehouse Updated From Admin"
#             quantity = obj.stock_quantity - obj.locked_quantity

#         obj.save()
#         user = request.user
#         models.ProductWarehouseLog.objects.create(
#             product_warehouse=obj,
#             event_type=event_type,
#             user=user,
#             quantity=quantity,
#             remark="Event description or additional information",
#         )

#     def delete_model(self, request, obj):
#         event_type = "Product Warehouse Deleted"
#         user = request.user
#         quantity = obj.stock_quantity
#         models.ProductWarehouseLog.objects.create(
#             product_warehouse=obj,
#             event_type=event_type,
#             user=user,
#             quantity=quantity,
#             remark="Event description or additional information",
#         )

#         obj.delete()

# admin.site.register(models.ProductWarehouse, ProductWarehouseAdmin)


# class ProductOfferAdmin(admin.ModelAdmin):

#     def save_model(self, request, obj, form, change):
#         if not change:
#             event_type = "Product Offer Created From Admin"
#         else:
#             event_type = "Product Offer Updated From Admin"

#         obj.save()
#         user = request.user
        
#         models.ProductOfferLog.objects.create(
#             offer_product=obj,
#             event_type=event_type,
#             user=user,
#             remark="Event description or additional information",
#         )

#     def delete_model(self, request, obj):
#         event_type = "Product Offer Deleted From Admin"
#         user = request.user
#         models.ProductOfferLog.objects.create(
#             offer_product=obj,
#             event_type=event_type,
#             user=user,
#             remark="Event description or additional information",
#         )

#         obj.delete()

# admin.site.register(models.ProductOffer, ProductOfferAdmin)