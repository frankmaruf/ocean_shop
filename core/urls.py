from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from graphene_django.views import GraphQLView
from core.qlschema import schema

urlpatterns = [
    path('admin/', admin.site.urls),
    # local_app
    path('inventory/',include('inventory.urls')),
    path('shop/',include('shop.urls')),
    # installed_apps
    path('ckeditor/',include('ckeditor_uploader.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path("graphql/", GraphQLView.as_view(graphiql=True, schema=schema)),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
]
if settings.DEBUG:
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]

