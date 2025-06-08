from django.urls import path
from . import views
from .views import ReviewListView, ReviewCreateView
from .views import CreateCafeView

urlpatterns = [
    path('', ReviewListView.as_view(), name='review_list'),
    path('nueva/', ReviewCreateView.as_view(), name='create_review'),
    path('cafes/', views.cafe_list, name='cafe_list'),
    path('cafes/<int:cafe_id>/', views.cafe_detail, name='cafe_detail'),
    path('cafes/<int:cafe_id>/fotos/', views.upload_photos, name='upload_photos'),
    path('cafes/nueva/', CreateCafeView.as_view(), name='create_cafe'),
    path('perfil/', views.owner_dashboard, name='owner_dashboard'),
    path('cafes/<int:cafe_id>/editar/', views.edit_cafe, name='edit_cafe'),
    path('cafes/<int:cafe_id>/eliminar/', views.delete_cafe, name='delete_cafe'),
]
