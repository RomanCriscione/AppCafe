from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login, logout, register (Django Allauth)
    path('accounts/', include('allauth.urls')),

    # Custom user actions (registro, editar avatar)
    path('users/', include('accounts.urls')),

    # Core (inicio, contacto, about)
    path('', include('core.urls')),

    # Cafeterías y reseñas
    path('reviews/', include('reviews.urls')),

    path('accounts/', include('django.contrib.auth.urls')),


]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
