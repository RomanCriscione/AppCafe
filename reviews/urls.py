from django.urls import path
from . import views
from django.views.generic import TemplateView
from . import views_claims

urlpatterns = [
    # Reseñas y cafés
    path('', views.ReviewListView.as_view(), name='review_list'),
    path('cafes/', views.CafeListView.as_view(), name='cafe_list'),
    path('cafes/nueva/', views.CreateCafeView.as_view(), name='create_cafe'),
    path('cafes/<int:cafe_id>/', views.cafe_detail, name='cafe_detail'),
    path('cafes/<int:cafe_id>/editar/', views.edit_cafe, name='edit_cafe'),
    path('cafes/<int:cafe_id>/eliminar/', views.delete_cafe, name='delete_cafe'),
    path('cafes/<int:cafe_id>/fotos/', views.upload_photos, name='upload_photos'),
    path('cafes/<int:cafe_id>/review/', views.create_review, name='create_review'),
    path('cafes/<int:cafe_id>/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('cafes/cercanos/', views.nearby_cafes, name='nearby_cafes'),
    path("owner/analytics/", views.analytics_dashboard, name="analytics_dashboard"),

    # Favoritos
    path('favoritos/', views.favorite_cafes, name='favorite_cafes'),

    # Panel del dueño
    path('perfil/', views.owner_dashboard, name='owner_dashboard'),
    path('mis-resenas/', views.owner_reviews, name='owner_reviews'),
    path('responder/<int:review_id>/', views.reply_review, name='reply_review'),
    path('owner/replies/<int:review_id>/', views.edit_owner_reply, name='edit_owner_reply'),
    path('owner/cambiar_visibilidad/<int:cafe_id>/', views.cambiar_visibilidad, name='cambiar_visibilidad'),
    path('planes/', views.planes_view, name='planes'),
    path('review/<int:review_id>/editar/', views.edit_review, name='edit_review'),
    path('review/<int:review_id>/eliminar/', views.delete_review, name='delete_review'),

    # Mapa
    path('mapa/', views.mapa_cafes, name='mapa_cafes'),

    path("cafes/<int:cafe_id>/claim/", views_claims.claim_start, name="claim_start"),
    path("cafes/<int:cafe_id>/claim/<int:claim_id>/verify/", views_claims.claim_verify_email, name="claim_verify_email"),
    path("cafes/<int:cafe_id>/claim/<int:claim_id>/evidence/", views_claims.claim_upload_evidence, name="claim_upload_evidence"),
    
]
