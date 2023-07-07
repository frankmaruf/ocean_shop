from django.db import models
from django.contrib.auth.models import User
from ckeditor_uploader.fields import RichTextUploadingField
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
import datetime
import random
from django.db.models import F


class DefaultField(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    deleted_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by', blank=True, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by', blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_deleted_by', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

class Category(DefaultField):
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    is_parent = models.BooleanField(default=True, blank=True, null=True)
    is_child_category = models.BooleanField(default=False, blank=True, null=True)
    description = RichTextUploadingField(blank=True, null=True,)
    slug = models.SlugField(max_length=100, unique=True)


    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        if self.parent:
            self.is_child_category = False

        if not self.parent:
            self.is_child_category = True

        super().save(*args, **kwargs)

    @property
    def parent_category(self):
        if self.is_child_category:
            return self.parent.name if self.parent else None
        else:
            return None


class Brand(DefaultField):
    name = models.CharField(max_length=100, unique=True)
    description = RichTextUploadingField(blank=True, null=True)
    slug = models.SlugField(max_length=100 , db_index=True, unique=True)

    def clean(self):
        super().clean()
        if len(self.name) <= 1:
            raise ValidationError("Name is too short")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductCategories(DefaultField):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='product_category')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='product_category')

    class Meta:
        unique_together = ('product', 'category')

class Product(DefaultField):
    name = models.CharField(max_length=100)
    categories = models.ManyToManyField(Category, through='ProductCategories', related_name='product_categories', blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, blank=True, null=True)
    description = RichTextUploadingField(blank=True, null=True)
    image = models.ImageField(upload_to='products/images/', blank=True, null=True)
    slug = models.SlugField(max_length=250, db_index=True, unique=True)

    def clean(self):
        super().clean()
        if len(self.name) <= 5:
            raise ValidationError("Name is too short")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        if self.image:
            current_year = datetime.date.today().year
            current_month = datetime.date.today().month
            current_day = datetime.date.today().day
            file_name = default_storage.get_available_name(self.image.name)
            image_path = f'products/images/'
            file_path = default_storage.save(f'{image_path}/{self.id}/{current_year}{current_month:02d}{current_day:02d}{file_name}', ContentFile(self.image.read()))
            self.image = file_path

        super().save(*args, **kwargs)

        if self.categories.exists():
            for category in self.categories.all():
                ProductCategories.objects.get_or_create(product=self, category=category)

class ProductRelatedImage(DefaultField):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_related_images')
    product_image = models.ImageField(upload_to='products/images/')
    position = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.image:
            current_year = datetime.date.today().year
            current_month = datetime.date.today().month
            current_day = datetime.date.today().day
            file_name = default_storage.get_available_name(self.image.name)
            image_path = f'products/images/{self.product.id}/related_images/'
            file_path = default_storage.save(f'{image_path}{current_year}{current_month:02d}{current_day:02d}{file_name}', ContentFile(self.image.read()))
            self.image = file_path
        super().save(*args, **kwargs)



class Size(DefaultField):
    name = models.CharField(max_length=20)

    def clean(self):
        super().clean()
        if len(self.name) <= 1:
            raise ValidationError("Name is too short")

    def __str__(self):
        return self.name

class ProductSize(DefaultField):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_size')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, related_name='product_size')

    class Meta:
        unique_together = ('product', 'size')


class Color(DefaultField):
    name = models.CharField(max_length=20)
    hex = models.CharField(max_length=20)

    def clean(self):
        super().clean()
        if len(self.name) <= 1:
            raise ValidationError("Name is too short")

    def __str__(self):
        return self.name


class ProductColor(DefaultField):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_color')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name='product_color')

    class Meta:
        unique_together = ('product', 'color')


class ProductSKU(DefaultField):
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_sku')
    size = models.ForeignKey('Size', on_delete=models.CASCADE, related_name='product_sku_size', blank=True, null=True)
    color = models.ForeignKey('Color', on_delete=models.CASCADE, related_name='product_sku_color', blank=True, null=True)
    product_image = models.ForeignKey(ProductRelatedImage, on_delete=models.CASCADE, blank=True, null=True)
    price = models.DecimalField(decimal_places=2, default=0.0, max_digits=10)
    maintain_stock = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):

        if not self.size:
            ProductSize.objects.create(product_id= self.product.id,size_id= self.size.id)

        if not self.color:
            ProductColor.objects.create(product_id= self.product.id, color_id= self.color.id)

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

class ProductSKURelatedImage(DefaultField):
    product_sku = models.ForeignKey(ProductSKU, on_delete=models.CASCADE, related_name='product_sku_related_images')
    product_image = models.ForeignKey(ProductRelatedImage, on_delete=models.CASCADE, related_name='product_sku_related_images')


class ProductOffer(DefaultField):
    product_sku = models.ForeignKey(ProductSKU, on_delete=models.CASCADE, related_name='product_sku_offers')
    price = models.DecimalField(decimal_places=2, default=0.0, max_digits=10)
    maintain_stock = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def clean(self):
        super().clean()
        if self.start_time >= self.end_time:
            raise ValidationError("The start time must be earlier than the end time.")


class Attribute(DefaultField):
    attribute_name = models.CharField(max_length=100)

    def clean(self):
        super().clean()
        if len(self.attribute_name) <= 1:
            raise ValidationError("Attribute Name is too short")

    def __str__(self):
        return f"{self.attribute_name}"


class AttributeValues(DefaultField):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='attribute_values')
    attribute_values_name = models.CharField(max_length=100)

    def clean(self):
        super().clean()
        if len(self.attribute_values_name) <= 1:
            raise ValidationError("Attribute Values Name is too short")

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