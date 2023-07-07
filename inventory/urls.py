
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from inventory import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'api/products', views.ProductViewSet, basename='products')

# Move ProductListView and APIProductDetails APIView to viewsets.ViewSet
# Check this view for Filter https://www.youtube.com/watch?v=-eTpoUStUi4&list=PLOLrQ9Pn6cawHF2lVl9goEm9Ta3rlutPD&index=14
# https://www.youtube.com/watch?v=nCGpaCrr1JQ&list=PLOLrQ9Pn6cawHF2lVl9goEm9Ta3rlutPD&index=15
# https://www.youtube.com/watch?v=k0oHOCutoII&list=PLOLrQ9Pn6cawHF2lVl9goEm9Ta3rlutPD&index=19
# https://www.youtube.com/watch?v=k0oHOCutoII&list=PLOLrQ9Pn6cawHF2lVl9goEm9Ta3rlutPD&index=19
# https://www.youtube.com/watch?v=xHZ74xF72OQ&list=PLOLrQ9Pn6cawHF2lVl9goEm9Ta3rlutPD&index=22

urlpatterns = [
]
urlpatterns.extend(router.urls)