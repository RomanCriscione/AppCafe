from django.urls import path
from . import views
from .views import ReviewListView, ReviewCreateView, CreateCafeView, favorite_cafes, toggle_favorite, mapa_cafes, CafeListView, create_review


urlpatterns = [
    path('', ReviewListView.as_view(), name='review_list'),
    path('cafes/', CafeListView.as_view(), name='cafe_list'),
    path('cafes/<int:cafe_id>/', views.cafe_detail, name='cafe_detail'),
    path('cafes/<int:cafe_id>/fotos/', views.upload_photos, name='upload_photos'),
    path('cafes/nueva/', CreateCafeView.as_view(), name='create_cafe'),
    path('perfil/', views.owner_dashboard, name='owner_dashboard'),
    path('cafes/<int:cafe_id>/editar/', views.edit_cafe, name='edit_cafe'),
    path('cafes/<int:cafe_id>/eliminar/', views.delete_cafe, name='delete_cafe'),
    path('responder/<int:review_id>/', views.reply_review, name='reply_review'),
    path('mis-resenas/', views.owner_reviews, name='owner_reviews'),
    path('cafes/<int:cafe_id>/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('favoritos/', favorite_cafes, name='favorite_cafes'),
    path('owner/replies/<int:review_id>/', views.edit_owner_reply, name='edit_owner_reply'),
    path('cafes/cercanos/', views.nearby_cafes, name='nearby_cafes'),
    path('owner/cambiar_visibilidad/<int:cafe_id>/', views.cambiar_visibilidad, name='cambiar_visibilidad'),
    path('planes/', views.planes_view, name='planes'),
    path('mapa/', mapa_cafes, name='mapa_cafes'),
    path("cafes/<int:cafe_id>/review/", create_review, name="create_review"),
    
]
