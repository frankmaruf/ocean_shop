from shop import models
from django.db import transaction
import random
from faker import Faker
from django.utils.text import slugify
from django.db.models import Count
fake = Faker()

@transaction.atomic
def generate_fake_data():

    categories = [
        models.Category(name=f"{fake.word()} {fake.word()} {fake.word()}",slug="-".join([fake.word(),fake.word(),fake.word(),fake.word(),str(random.randint(1000,9999))]),description=fake.sentence(),is_parent=random.choice([True, False]))
        for _ in range(100)
    ]
    models.Category.objects.bulk_create(categories)

    brands = [
        models.Brand(name=f"{fake.word()} {fake.word()}",description=fake.sentence(),slug="-".join([fake.word(),fake.word(),fake.word(),fake.word(),fake.word(),str(random.randint(1000,9999))]))
        for _ in range(100)
    ]

    models.Brand.objects.bulk_create(brands)

    total_categories = models.Category.objects.aggregate(total=Count('id'))['total']


    products = [
    models.Product(
        name=fake.word(),
        brand= random.choice(models.Brand.objects.all()),
        description=fake.sentence(),
        slug="-".join([fake.word(),fake.word(),fake.word(),fake.word(),str(random.randint(1000,9999))])
    )
    for _ in range(100)
    ]

    created_products = models.Product.objects.bulk_create(products)

    for product in models.Product.objects.all():
        num_categories = min(random.randint(1, 3), total_categories)
        random_categories = random.sample(list(models.Category.objects.all()), k=num_categories)
        product.save()
        product.categories.set(random_categories)


    sizes = [
        models.Size(name=fake.word())
        for _ in range(100)
        ]

    models.Size.objects.bulk_create(sizes)


    color = [
        models.Color(name=fake.word(),hex=fake.hex_color())
        for _ in range(100)
        ]

    models.Color.objects.bulk_create(color)


    products = models.Product.objects.all()
    sizes = models.Size.objects.all()
    colors = models.Color.objects.all()
    skus = []

    for _ in range(100):
        product = random.choice(products)
        size = random.choice(sizes)
        color = random.choice(colors)
        price = random.uniform(10, 100)
        stock = random.randint(1, 15)

        sku = models.ProductSKU(product=product, size=size, color=color, price=price, stock=stock)
        skus.append(sku)

    models.ProductSKU.objects.bulk_create(skus)

    attributes = [
        models.Attribute(attribute_name=fake.word())
        for _ in range(100)
    ]

    models.Attribute.objects.bulk_create(attributes)

    attribute_values = [
        models.AttributeValues(attribute=random.choice(models.Attribute.objects.all()),attribute_values_name=fake.word())
        for _ in range(100)
    ]
    models.AttributeValues.objects.bulk_create(attribute_values)

    for _ in range(3):
        for _ in range(50):
            product_attribute_values = [
                models.ProductAttributeValues(
                    product=random.choice(models.Product.objects.all()),
                    attribute_value=random.choice(models.AttributeValues.objects.all())
                )
                for _ in range(5)
            ]

            existing_product_attribute_values = models.ProductAttributeValues.objects.filter(
                product__in=[obj.product for obj in product_attribute_values],
                attribute_value__in=[obj.attribute_value for obj in product_attribute_values]
            )
            existing_product_attribute_values_set = set(
                (obj.product_id, obj.attribute_value_id) for obj in existing_product_attribute_values
            )

            new_product_attribute_values = [
                obj
                for obj in product_attribute_values
                if (obj.product_id, obj.attribute_value_id) not in existing_product_attribute_values_set
            ]
            models.ProductAttributeValues.objects.bulk_create(new_product_attribute_values)

def run():
    generate_fake_data()
