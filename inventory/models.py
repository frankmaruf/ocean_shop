from django.db import models
from django.contrib.auth.models import User
from ckeditor_uploader.fields import RichTextUploadingField
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.db.utils import IntegrityError
from pathlib import Path
from django.db.models import Min
import datetime
import calendar
import shutil
from django.conf import settings
import random
import os
from django.db.models import F
from django.utils import timezone
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.db import connection
from threadlocals.threadlocals import get_current_request
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404


class DefaultField(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by', blank=True, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by', blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_deleted_by', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Warehouse(DefaultField):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def clean(self):
        if len(self.name) <= 2:
            raise ValidationError("Name is too short")
        return super().clean()

    def save(self,*args, **kwargs):
        self.name = self.name.strip().title()
        if self.address:
            self.address = self.address.strip()
        if self.city:
            self.city = self.city.strip()
        if self.state:
            self.state = self.state.strip()
        if self.country:
            self.country = self.country.strip()
        if self.postal_code:
            self.postal_code = self.postal_code.strip()
        if self.capacity:
            self.capacity = self.capacity
        if self.description:
            self.description = self.description.strip()
        super().save(*args, **kwargs)


class ProductStockStatus(DefaultField):
    status_name = models.CharField(max_length=100, unique=True)

    def clean(self):

        if self.__class__.objects.count() >= 10:
            raise ValidationError("Status can't be more than 10.")

        if len(self.status_name) <= 2:
            raise ValidationError("Status Name is too short")
        return super().clean()

    def save(self,*args, **kwargs):
        self.name = self.status_name.strip().title()
        super().save(*args, **kwargs)


class Brand(DefaultField):
    name = models.CharField(max_length=100, unique=True)
    description = RichTextUploadingField(blank=True, null=True)
    slug = models.SlugField(max_length=100 , db_index=True, unique=True, blank=True, null=True)

    def clean(self):
        if len(self.name) <= 1:
            raise ValidationError("Name is too short")
        return super().clean()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.strip().title()
        if self.description:
            self.description = self.description.strip()
        if not self.slug:
            self.slug = slugify(self.name.strip())

        else:
            self.slug = self.slug.strip()

        super().save(*args, **kwargs)


def category_icon_upload_path(instance,filename):
    if instance.id:
        random_number = random.randint(100, 999)
        return f"category/{instance.id}/icon/{random_number}{filename}"
    else:
        return filename

def category_logo_upload_path(instance,filename):
    if instance.id:
        random_number = random.randint(100, 999)
        return f"category/{instance.id}/logo/{random_number}{filename}"
    else:
        return filename

def category_banner_upload_path(instance,filename):
    if instance.id:
        random_number = random.randint(100, 999)
        return f"category/{instance.id}/banner/{random_number}{filename}"
    else:
        return filename

class Category(DefaultField):
    name = models.CharField(max_length=100, unique=True)
    icon = models.ImageField(upload_to=category_icon_upload_path, blank=True, null=True)
    font_awesome = models.CharField(max_length=50,blank=True, null=True)
    logo = models.ImageField(upload_to=category_logo_upload_path, blank=True, null=True)
    banner = models.ImageField(upload_to=category_banner_upload_path, blank=True, null=True)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    is_parent = models.BooleanField(default=True, blank=True, null=True)
    is_child_category = models.BooleanField(default=False, blank=True, null=True)
    description = RichTextUploadingField(blank=True, null=True,)
    slug = models.SlugField(max_length=100, unique=True)
    def __str__(self):
        return self.name

    def clean(self):
        if len(self.name) <= 1:
            raise ValidationError("Name is too short")
        if self.icon and self.font_awesome:
            raise ValidationError("Only icon or the font_awesome can be select")
        return super().clean()

    def save(self, *args, **kwargs):

        if self.id:
            existing = get_object_or_404(Category,id=self.id)
            if existing.icon != self.icon:
                existing.icon.delete(save=False)

            if existing.logo != self.logo:
                existing.logo.delete(save=False)

            if existing.banner != self.banner:
                existing.banner.delete(save=False)

        self.name = self.name.title()

        if not self.slug:
            self.slug = slugify(self.name)

        if self.parent:
            self.is_parent = False
            self.is_child_category = True
        elif not self.parent:
            self.is_parent = True
            self.is_child_category = False

        if not self.id:
            super().save(*args, **kwargs)
            if self.banner:
                file_name = default_storage.get_available_name(self.banner.name)
                random_number = random.randint(100, 999)
                file_path = default_storage.save(f'category/{self.id}/banner/{random_number}{file_name}', ContentFile(self.banner.read()))
                self.banner = file_path
            if self.icon:
                file_name = default_storage.get_available_name(self.icon.name)
                random_number = random.randint(100, 999)
                file_path = default_storage.save(f'category/{self.id}/icon/{random_number}{file_name}', ContentFile(self.icon.read()))
                self.icon = file_path
            if self.logo:
                file_name = default_storage.get_available_name(self.logo.name)
                random_number = random.randint(100, 999)
                file_path = default_storage.save(f'category/{self.id}/logo/{random_number}{file_name}', ContentFile(self.logo.read()))
                self.logo = file_path

        super().save(*args, **kwargs)

    @receiver(models.signals.pre_delete,sender="inventory.Category")
    def category_delete_files(sender,instance, **kwargs):
        for field in instance._meta.fields:
            # if field.name == "icon":
            #     file = getattr(instance,field.name)
            #     if file:
            #         file.delete(save=False)

            if field.name == "id":
                BASE_DIR = settings.BASE_DIR
                MEDIA_ROOT  = os.path.join(BASE_DIR, 'media')
                folder_path = os.path.join(MEDIA_ROOT, f"category/{instance.id}/")
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)


    @property
    def parent_category(self):
        if self.is_child_category:
            return self.parent.name if self.parent else None
        else:
            return None


class ProductCategories(DefaultField):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='product_category_list')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_product_list')

    class Meta:
        unique_together = ('product', 'category')


class Tag(DefaultField):
    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True)

    def clean(self):
        if len(self.name) <= 2 or self.__class__.objects.filter(name=self.name.strip().title()).exists():
            raise ValidationError("Name is too short or exist")
        return super().clean()

    def save(self, *args, **kwargs):
        self.name = self.name.strip().title()
        if not self.slug:
            self.slug = slugify(self.name.strip())
        super().save(*args, **kwargs)


class ProductTags(DefaultField):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='product_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='tag_products')

    class Meta:
        unique_together = ('product', 'tag')

class UnitOfMeasurementType(DefaultField):
    name = models.CharField(max_length=100, unique=True)

    def clean(self):
        if len(self.name) <= 1:
            raise ValidationError("Name is too short")
        return super().clean()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.name = self.name.strip().title()
        super().save(*args, **kwargs)


class UnitOfMeasurement(DefaultField):
    name = models.CharField(max_length=100, unique=True)
    type = models.ForeignKey(UnitOfMeasurementType, on_delete=models.CASCADE, related_name='uom')

    def clean(self):
        if len(self.name) <= 5:
            raise ValidationError("Name is too short")
        return super().clean()

    def save(self, *args, **kwargs):
        self.name = self.name.strip().title()
        super().save(*args, **kwargs)


class ProductUnitOfMeasurement(DefaultField):
    product = models.OneToOneField("Product", on_delete=models.CASCADE, related_name='product_uom')
    unit_of_measurement = models.ForeignKey(UnitOfMeasurement, on_delete=models.CASCADE, related_name='product_ufm')
    stock_unit = models.DecimalField(decimal_places=2, default=0.0, max_digits=10)


class ProductBrand(DefaultField):
    product = models.OneToOneField("Product", on_delete=models.CASCADE, related_name='product_brand')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='brand_product')
    model = models.CharField(max_length=100)


class ProductColor(DefaultField):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name='product_colors')
    color = models.ForeignKey("Color", on_delete=models.CASCADE, related_name='color_products')

    class Meta:
        unique_together = ('product', 'color')


def product_image_upload_path(instance,filename):
    random_number = random.randint(100, 999)
    return f"products/images/{instance.id}/{random_number}{filename}"


class Product(DefaultField):
    name = models.CharField(max_length=100)
    categories = models.ManyToManyField(Category, through=ProductCategories, related_name='product_categories', blank=True)
    tags = models.ManyToManyField(Tag, through=ProductTags, related_name='product_tags', blank=True)
    description = RichTextUploadingField(blank=True, null=True)
    image = models.ImageField(upload_to=product_image_upload_path, blank=True, null=True)
    slug = models.SlugField(max_length=250, db_index=True, unique=True)

    def clean(self):
        if len(self.name) <= 5:
            raise ValidationError("Name is too short")
        return super().clean()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.id:
            existing = get_object_or_404(Product,id=self.id)
            if existing.image != self.image:
                existing.image.delete(save=False)

        if not self.slug:
            self.slug = slugify(self.name)

        self.name = self.name.title()

        super().save(*args, **kwargs)

        if self.categories.exists():
            for category in self.categories.all():
                ProductCategories.objects.get_or_create(product=self, category=category)

        if self.tags.exists():
            for tag in self.tags.all():
                ProductTags.objects.get_or_create(product=self, tag=tag)

    @receiver(models.signals.pre_delete,sender="inventory.Product")
    def product_delete_files(sender,instance, **kwargs):
        for field in instance._meta.fields:
            if field.name == "image":
                file = getattr(instance,field.name)
                if file:
                    file.delete(save=False)

    @property
    def sku_products(self):
        return self.product_variations

class ProductSEO(DefaultField):
    product = models.OneToOneField(Product, related_name="product_seo", on_delete=models.CASCADE)
    meta_title = models.CharField(max_length=250)
    meta_description = models.TextField(max_length=250, blank=True, null=True)
    meta_keywords = models.CharField(max_length=250, blank=True, null=True)

    def clean(self) -> None:
        if self.meta_keywords and "," not in self.meta_keywords:
            raise ValidationError("Meta Keywords must be separated by coma(',')  ")
        return super().clean()

    def save(self,*args, **kwargs):
        self.meta_title = self.meta_title.strip().title()
        if self.meta_description:
            self.meta_description = self.meta_description.strip()
        if self.meta_keywords and "," in self.meta_description:
            self.meta_description = self.meta_description.strip()

        super().save(*args, **kwargs)


class Color(DefaultField):
    name = models.CharField(max_length=20)
    hex = models.CharField(max_length=20)

    def clean(self):
        if len(self.name) <= 1:
            raise ValidationError("Name is too short")
        return super().clean()

    def __str__(self):
        return self.name


class ProductSKU(DefaultField):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_variations')
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    upc = models.CharField(max_length=100, unique=True, blank=True, null=True)
    ean = models.CharField(max_length=100, unique=True, blank=True, null=True)
    min_min = models.PositiveIntegerField(blank=True, null=True)
    max_max = models.PositiveIntegerField(blank=True, null=True)
    uom = models.ForeignKey('ProductUnitOfMeasurement', on_delete=models.SET_NULL, related_name='uof_sku_products', blank=True, null=True)
    color = models.ForeignKey('ProductColor', on_delete=models.CASCADE, related_name='color_sku_products', blank=True, null=True)
    product_image = models.ForeignKey("ProductRelatedImage", on_delete=models.CASCADE, blank=True, null=True)
    maintain_stock = models.BooleanField(default=True)
    qty = models.PositiveIntegerField(default=0)
    subtract_stock = models.BooleanField(default=True)
    stock_status = models.ForeignKey(ProductStockStatus, on_delete=models.CASCADE, related_name='product_stock_status')

    class Meta:
        unique_together = ('product', 'uom', 'color')

    def clean(self):
        if self.uom and not self.__class__.objects.filter(uom__product_id=self.product.id).exists():
            raise ValidationError("The Product Unit Of Measurement instance must have the same product you have selected")

        if self.color and not self.__class__.objects.filter(color__product_id=self.product.id).exists():
            raise ValidationError("The Product Color instance must have the same product you have selected")
        return super().clean()

    def save(self, *args, **kwargs):

        if not self.sku:
            current_year = datetime.date.today().year
            brand_name = self.product.brand.name if (self.product.brand and hasattr(self.product.brand, 'name')) else "BOSP"
            product_name = self.product.name
            current_year = datetime.date.today().year
            current_month = datetime.date.today().month
            current_day = datetime.date.today().day
            product_category = ProductCategories.objects.filter(product_id=self.product.id).first()
            category = product_category.name if product_category else None

            random_number = random.randint(100, 999)
            if brand_name and len(brand_name) >=2 and category and len(category) >= 2:
                sku = f"{current_year}{product_name[:1]}{product_name[-1:]}{random_number}{brand_name[:1]}{brand_name[-1:]}{category[:1]}{category[-1:]}{current_month:02d}{current_day:02d}".upper()
            else:
                sku = f'{product_name[:1]}{product_name[-1:]}{random_number}{current_year}{current_month:02d}{current_day:02d}'.upper()

            self.sku = sku

        super().save(*args, **kwargs)

    @property
    def unit_price(self):
        return self.product_sku_price.unit_price

    @property
    def is_in_stock(self):
        return self.qty>0

    @property
    def sale_price(self):
        return self.product_sku_price.sale_price

    @property
    def total_percent_off(self):
        if self.offer_price is None:
            return None

        percent_off = ((self.sale_price - self.offer_price) / self.sale_price) * 100
        return round(percent_off, 2)

    @property
    def stock_locations(self):
        return self.product_warehouses.filter(available_qty__gt=0, stock_quantity__gt=0).all()

    @property
    def related_images(self):
        return self.product_sku_related_images

    @property
    def warehouse_stock_quantity(self):
        return sum(product_warehouse.stock_quantity for product_warehouse in self.product_warehouses.all() if hasattr(self, "product_warehouses"))


def product_related_image(instance,filename):
    random_number = random.randint(100, 999)
    return f"products/{instance.product.id}/images/related_images/{random_number}{filename}"



class ProductRelatedImage(DefaultField):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_related_images')
    product_image = models.ImageField(upload_to=product_related_image)
    position = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.id:
            existing = get_object_or_404(ProductRelatedImage,id=self.id)
            if existing.product_image != self.product_image:
                existing.product_image.delete(save=False)
        super().save(*args, **kwargs)

    @receiver(models.signals.pre_delete,sender="inventory.ProductRelatedImage")
    def related_files_delete(sender,instance, **kwargs):
        for field in instance._meta.fields:
            if field.name == "product_image":
                file = getattr(instance,field.name)
                if file:
                    file.delete(save=False)


class ProductSKURelatedImage(DefaultField):
    product_sku = models.ForeignKey(ProductSKU, on_delete=models.CASCADE, related_name='product_sku_related_images')
    product_image = models.ForeignKey(ProductRelatedImage, on_delete=models.CASCADE, related_name='product_sku_related_images')


class Attribute(DefaultField):
    attribute_name = models.CharField(max_length=100)
    position = models.IntegerField(default=0)

    def clean(self):
        if len(self.attribute_name) <= 1:
            raise ValidationError("Attribute Name is too short")
        return super().clean()

    def __str__(self):
        return f"{self.attribute_name}"


class AttributeValues(DefaultField):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='attribute_values')
    attribute_values_name = models.CharField(max_length=100)
    position = models.IntegerField(default=0)

    def clean(self):
        if len(self.attribute_values_name) <= 1:
            raise ValidationError("Attribute Values Name is too short")
        return super().clean()

    def __str__(self):
        return str(self.attribute_values_name)


class ProductAttributeValues(DefaultField):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_attribute_values")
    attribute_value = models.ForeignKey(AttributeValues, on_delete=models.CASCADE, related_name="product_attribute_values")
    position = models.IntegerField(default=0)

    class Meta:
        unique_together = ('product', 'attribute_value')

    def __str__(self):
        return f"{self.attribute_value.attribute}---->{self.attribute_value.attribute_values_name}"

    def save(self, *args, **kwargs):
        try:
            self.full_clean()
            super().save(*args, **kwargs)
        except IntegrityError:
            existing_record = ProductAttributeValues.objects.filter(
                product=self.product,
                attribute_value=self.attribute_value,
            ).first()
            if existing_record:
                existing_record.position = F('position') + 1
                existing_record.save()

    @property
    def attribute(self):
        return self.attribute_value.attribute


class FilterGroup(DefaultField):
    name = models.CharField(max_length=100, unique=True)

    def clean(self):
        if len(self.name.strip()) <= 1 or self.__class__.objects.filter(name=self.name.strip().title()).exists():
            raise ValidationError("Something Went Wrong")
        return super().clean()

    def __str__(self):
        return f"{self.name}"

    def save(self,*args, **kwargs):
        self.name = self.name.strip().title()
        super().save(*args, **kwargs)


class Filter(DefaultField):
    filter_group = models.ForeignKey(FilterGroup, on_delete=models.CASCADE, related_name='filter_group_filters')
    name = models.CharField(max_length=100)
    position = models.IntegerField(default=0)


    class Meta:
        unique_together = ('filter_group', 'name')

    def clean(self):
        if len(self.name.strip()) <= 1 or self.__class__.objects.filter(filter_group=self.filter_group,name=self.name.strip().title()).exists():
            raise ValidationError("Something Went Wrong")
        return super().clean()

    def __str__(self):
        return f"{self.name} -> {self.filter_group}"

    def save(self,*args, **kwargs):
        self.name = self.name.strip().title()
        super().save(*args, **kwargs)


class ProductFilter(DefaultField):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_filters")
    filter = models.ForeignKey(Filter, on_delete=models.CASCADE, related_name="product_filters")
    position = models.IntegerField(default=0)

    class Meta:
        unique_together = ('product', 'filter')

    def __str__(self):
        return f"{self.product}---->{self.filter}"

    @property
    def filter_group(self):
        return self.filter.filter_group


class StockEntryPurpose(DefaultField):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def clean(self):
        if len(self.name.strip()) <= 1 or self.__class__.objects.filter(name=self.name.strip().title()).exists():
            raise ValidationError("Something Went Wrong W")
        return super().clean()

    def save(self, *args, **kwargs):
        self.name = self.name.strip().title()
        if self.description:
            self.description = self.description.strip()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductWarehouse(DefaultField):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_warehouses')
    sku= models.CharField(max_length=100, blank=True, null=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='warehouse_products')
    entry_purpose = models.ForeignKey(StockEntryPurpose, on_delete=models.CASCADE, related_name='entry_purpose_products')
    remark = models.CharField(max_length=100)
    stock_quantity = models.PositiveIntegerField(default=0)
    locked_quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'warehouse')

    def __str__(self):
        return f'{self.product} - {self.warehouse}'

    @property
    def sc_stock_quantity(self):
        return self.product_warehouses_serial_code_products.count() if hasattr(self,"product_warehouses_serial_code_products") else None


    @property
    def available_qty(self):
        if self.sc_stock_quantity:
            return self.sc_stock_quantity - self.locked_quantity
        else:
            return self.stock_quantity - self.locked_quantity


class ProductWarehouseSerialCode(models.Model):
    product_warehouse = models.ForeignKey(ProductWarehouse, on_delete=models.CASCADE, related_name='product_warehouses_serial_code_products')
    serial_code = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(User, related_name='%(class)s_created_by',on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

# ----------- Product WareHouse SerialCode Signal Function Start ----------#
@receiver(post_save, sender=ProductWarehouseSerialCode)
def create_product_warehouse_serial_code(sender, instance, created, **kwargs):
    request = get_current_request()
    user = request.user
    if created:
        instance.created_by = user

# ----------- Product WareHouse SerialCode Signal Function End ----------#

class ProductWarehouseLog(models.Model):
    product_warehouse = models.ForeignKey(ProductWarehouse, on_delete=models.SET_NULL, null=True,blank=True, related_name='warehouse_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=100)
    event_date = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField(default=0)
    remark = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f'{self.event_type} - {self.product_warehouse}'

    @classmethod
    def truncate(cls):
        current_year = datetime.date.today().year
        current_month = datetime.date.today().month
        current_day = datetime.date.today().day
        last_day = calendar.monthrange(current_year, current_month)[1]

        if last_day != current_day:
            raise ValidationError("Truncate method can only be called on the last day of the month.")

        with connection.cursor() as cursor:
            cursor.execute('TRUNCATE TABLE "{0}" CASCADE'.format(cls._meta.db_table))

    class Meta:
        ordering = ['-event_date']

# ----------- Product WareHouse Signal Function Start ----------#
@receiver(post_save, sender=ProductWarehouse)
def create_product_warehouse_log(sender, instance, created, **kwargs):
    request = get_current_request()
    user = request.user
    if created:
        event_type = "Product Warehouse Created"
    else:
        event_type = "Product Warehouse Updated"
        quantity = instance.stock_quantity - instance.locked_quantity

    ProductWarehouseLog.objects.create(
        product_warehouse=instance,
        event_type=event_type,
        quantity=quantity,
        user = user,
        remark="Event description or additional information",
    )


@receiver(pre_delete, sender=ProductWarehouse)
def delete_product_warehouse_log(sender, instance, **kwargs):
    event_type = "Product Warehouse Deleted"
    request = get_current_request()
    user = request.user
    quantity = instance.stock_quantity

    ProductWarehouseLog.objects.create(
        product_warehouse=instance,
        event_type=event_type,
        quantity=quantity,
        remark="Event description or additional information",
        user = user,
    )

# ----------- Product WareHouse Signal Function End ----------#
class OfferType(DefaultField):
    type = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='offers/product/logo/', blank=True, null=True)
    banner = models.ImageField(upload_to='offers/product/banner/', blank=True, null=True)
    show_reminder = models.BooleanField(default=False)

    def clean(self):
        return super().clean()

    # def save(self, *args, **kwargs):
    #     if self.logo:
    #         current_year = datetime.date.today().year
    #         current_month = datetime.date.today().month
    #         current_day = datetime.date.today().day
    #         file_name = default_storage.get_available_name(self.logo.name)
    #         image_path = f'offers/product/logo/'
    #         file_path = default_storage.save(f'{image_path}{self.id}/{current_year}/{current_month:02d}/{current_day:02d}/{file_name}', ContentFile(self.logo.read()))
    #         self.logo = file_path

    #     if self.banner:
    #         current_year = datetime.date.today().year
    #         current_month = datetime.date.today().month
    #         current_day = datetime.date.today().day
    #         file_name = default_storage.get_available_name(self.banner.name)
    #         image_path = f'offers/product/banner/'
    #         file_path = default_storage.save(f'{image_path}/{self.id}/{current_year}/{current_month:02d}/{current_day:02d}/{file_name}', ContentFile(self.logo.read()))
    #         self.banner = file_path
    #     super().save(*args, **kwargs)


class ProductOffer(DefaultField):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_offers', blank=True, null=True)
    product_sku = models.ForeignKey(ProductSKU, on_delete=models.CASCADE, related_name='product_sku_offers', blank=True, null=True)
    maintain_stock = models.BooleanField(default=True)
    show_reminder = models.BooleanField(default=False)
    type = models.ForeignKey(OfferType, on_delete=models.CASCADE, related_name='offer_type_products')
    offer_stock = models.PositiveIntegerField(default=0)
    offer_price = models.DecimalField(decimal_places=2, default=0.0, max_digits=10)
    max_stock = models.PositiveIntegerField(blank=True, null=True)
    min_stock = models.PositiveIntegerField(default=1, blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    def get_earliest_offer(self):
        if self.product:
            offers = ProductOffer.objects.filter(product=self.product)
        elif self.product_sku:
            offers = ProductOffer.objects.filter(product_sku=self.product_sku)
        else:
            return None, None

        current_time = timezone.now()

        future_offers = offers.filter(end_time__gte=current_time, start_time__lte=current_time)

        if future_offers.exists():
            min_start_time = future_offers.aggregate(Min('start_time'))['start_time__min']
            earliest_offer = future_offers.filter(start_time=min_start_time).first()
            lowest_upcoming_datetime_object = offers.filter(start_time__gt=earliest_offer.end_time)
            lowest_upcoming_datetime = lowest_upcoming_datetime_object.aggregate(Min('start_time'))['start_time__min']
            lowest_upcoming_datetime_id = lowest_upcoming_datetime_object.filter(start_time=lowest_upcoming_datetime).values_list('id', flat=True).first()
            return earliest_offer, earliest_offer.id, lowest_upcoming_datetime, lowest_upcoming_datetime_id

        return None, None, None, None

    @property
    def running_id(self):
        _, id,_,_ = self.get_earliest_offer()
        return id

    @property
    def is_running(self):
        earliest_offer, _, _, _ = self.get_earliest_offer()
        return earliest_offer

    @property
    def offer_type(self):
        earliest_offer, _,_, _ = self.get_earliest_offer()
        return earliest_offer.type if earliest_offer else None

    @property
    def current_offer_price(self):
        earliest_offer, _,_ , _= self.get_earliest_offer()
        return earliest_offer.offer_price if earliest_offer else None

    @property
    def next_upcoming_offer_datetime(self):
        earliest_offer,_, lowest_upcoming_datetime, _ = self.get_earliest_offer()
        if earliest_offer and earliest_offer == self:
            return lowest_upcoming_datetime if any([self.show_reminder,self.type.show_reminder]) else None
        return

    @property
    def next_id(self):
        earliest_offer,_, _, lowest_upcoming_datetime_id = self.get_earliest_offer()
        if earliest_offer and earliest_offer == self:
            return lowest_upcoming_datetime_id if any([self.show_reminder,self.type.show_reminder]) else None
        return None


    def clean(self):

        if self.product and not hasattr(self.product,"product_prices"):
            raise ValidationError("Offer Product should have unit price")

        if self.product and self.offer_price and hasattr(self.product,"product_prices"):
            if self.offer_price < self.product.product_prices.latest('id').unit_price:
                raise ValidationError("Offer Price must be greater than the unit price")

        if self.product_sku and not hasattr(self.product_sku,"product_sku_prices"):
            raise ValidationError("That Product SKU should have unit price")

        if self.product_sku and self.offer_price and hasattr(self.product_sku,"product_sku_prices"):
            if self.product_sku.product_sku_prices.latest('id').unit_price < self.offer_price:
                raise ValidationError("Offer Price must be greater than the unit price")

        if self.start_time and self.end_time:
            overlapping_offers = self.__class__.objects.filter(
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            )
            if self.pk:
                overlapping_offers = overlapping_offers.exclude(pk=self.pk)

            if overlapping_offers.exists():
                raise ValidationError("An offer already exists within the specified time range.")

        if self.start_time and self.start_time >= self.end_time:
            raise ValidationError("The start time must be earlier than the end time.")

        if not self.offer_price:
            raise ValidationError("Must set the offer price")

        if self.min_stock and self.max_stock:
            if self.min_stock >= self.max_stock:
                raise ValidationError("The max stock must be greater than the min stock.")

        if not self.type:
            raise ValidationError("Type must be provided.")

        if not self.product and not self.product_sku:
            raise ValidationError("At least one field (product or product_sku) must be provided.")

        return super().clean()


class LabelType(DefaultField):
    name = models.CharField(max_length=100, unique=True)

    def clean(self):
        super().clean()
        if len(self.name) <= 2:
            raise ValidationError("Name is too sort")

    def save(self, *args, **kwargs):
        self.name = self.name.strip().title()
        super().save(*args, **kwargs)


class Label(DefaultField):
    label_type = models.OneToOneField(LabelType, related_name="label", on_delete=models.CASCADE)
    label_image = models.ImageField(upload_to='offers/label/images/', blank=True, null=True)
    label_text = models.CharField(max_length=100, unique=True, blank=True, null=True)

    def clean(self):
        super().clean()
        if self.label_image and self.label_text:
            raise ValidationError("Only one field can be used between label_image and label_text.")
        elif not self.label_image and not self.label_text:
            raise ValidationError("At least one field (label_image or label_text) must be provided.")
        elif self.label_text and len(self.label_text) <= 2:
            raise ValidationError("Text is too short.")

    def save(self, *args, **kwargs):
        if self.label_text:
            self.label_text = self.label_text.strip().title()

        super().save(*args, **kwargs)


class ProductLabel(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_label',blank=True, null=True)
    product_sku = models.ForeignKey(ProductSKU, on_delete=models.CASCADE, related_name='product_sku_label', blank=True, null=True)
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='label_product')

    class Meta:
        unique_together = ('product', 'label',"product_sku")

    def clean(self) -> None:
        if not self.product and not self.product_sku:
            raise ValidationError("Product Or Product Sku must be present.")
        return super().clean()


class ProductOfferLog(models.Model):
    offer_product = models.ForeignKey(ProductOffer, on_delete=models.SET_NULL, null=True,blank=True, related_name='offer_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=100)
    event_date = models.DateTimeField(default=timezone.now)
    remark = models.CharField(max_length=100 ,null=True, blank=True)

    def __str__(self):
        return f'{self.event_type} - {self.offer_product.product_sku.product.name}'

    @classmethod
    def truncate(cls):
        current_year = datetime.date.today().year
        current_month = datetime.date.today().month
        current_day = datetime.date.today().day
        last_day = calendar.monthrange(current_year, current_month)[1]

        if last_day != current_day:
            raise ValidationError("Truncate method can only be called on the last day of the month.")

        with connection.cursor() as cursor:
            cursor.execute('TRUNCATE TABLE "{0}" CASCADE'.format(cls._meta.db_table))

    class Meta:
        ordering = ['-event_date']


# ----------- Product Offer Log Signal Function Start ----------#
@receiver(post_save, sender=ProductOffer)
def create_product_offer_log(sender, instance, created, **kwargs):
    request = get_current_request()
    user = request.user
    if created:
        event_type = "Product Offer Created"
    else:
        event_type = "Product Offer Updated"

    ProductOfferLog.objects.create(
        offer_product=instance,
        event_type=event_type,
        user = user,
        # remark="Event description or additional information",
    )

@receiver(pre_delete, sender=ProductOffer)
def delete_product_offer_log(sender, instance, **kwargs):
    event_type = "Product Offer Deleted"
    request = get_current_request()
    user = request.user
    ProductOfferLog.objects.create(
        offer_product=instance,
        event_type=event_type,
        # remark="Event description or additional information",
        user = user,
    )

# ----------- Product Offer Log Signal Function End ----------#

class ProductSKUPrice(DefaultField):
    product_sku = models.ForeignKey(ProductSKU, on_delete=models.CASCADE, related_name='product_sku_prices')
    unit_price = models.DecimalField(decimal_places=2, default=0.0, max_digits=10)
    sale_price = models.DecimalField(decimal_places=2, default=0.0, max_digits=10)

    def clean(self):
        super().clean()
        if self.unit_price >= self.sale_price:
            raise ValidationError("Unit Price can't be greater than sale price")

    @property
    def current_sale_price(self):
        try:
            latest_price = self.product_sku.product_sku_prices.latest('id')
            return latest_price.unit_price
        except ObjectDoesNotExist:
            return 0.0

    @property
    def current_unit_price(self):
        try:
            latest_price = self.product_sku.product_sku_prices.latest('id')
            return latest_price.unit_price
        except ObjectDoesNotExist:
            return 0.0


class ProductPrice(DefaultField):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_prices')
    unit_price = models.DecimalField(decimal_places=2, default=0.0, max_digits=10)
    sale_price = models.DecimalField(decimal_places=2, default=0.0, max_digits=10)

    def clean(self):
        super().clean()
        if self.unit_price >= self.sale_price:
            raise ValidationError("Unit Price can't be greater than sale price")

    @property
    def current_sale_price(self):
        try:
            latest_price = self.product.product_prices.latest('id')
            return latest_price.sale_price
        except ObjectDoesNotExist:
            return 0.0

    @property
    def current_unit_price(self):
        try:
            latest_price = self.product.product_prices.latest('id')
            return latest_price.unit_price
        except ObjectDoesNotExist:
            return 0.0

class ProductDeliveryTimeLine(DefaultField):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='product_delivery_timeline')
    delivery_day_min = models.PositiveIntegerField(default=0)
    delivery_day_max = models.PositiveIntegerField(default=0)
    delivery_day_min_expedited = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        if self.delivery_day_min >= self.delivery_day_max:
            raise ValidationError("The max day must the greater than mix day")


class ProductSKUDeliveryTimeLine(DefaultField):
    product_sku = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='product_sku_delivery_timeline')
    delivery_day_min = models.PositiveIntegerField(default=0)
    delivery_day_max = models.PositiveIntegerField(default=0)
    delivery_day_min_expedited = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        if self.delivery_day_min >= self.delivery_day_max:
            raise ValidationError("The max day must the greater than mix day")


#-------------------Calling Signal-------------------#
post_save.connect(create_product_warehouse_serial_code, sender=ProductWarehouseSerialCode)
post_save.connect(create_product_warehouse_log, sender=ProductWarehouse)
post_save.connect(delete_product_warehouse_log, sender=ProductWarehouse)
post_save.connect(create_product_offer_log, sender=ProductOffer)
post_save.connect(delete_product_offer_log, sender=ProductOffer)