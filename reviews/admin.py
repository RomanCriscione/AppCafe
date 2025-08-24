from django.contrib import admin
from .models import Cafe, Review, CafeStat

@admin.register(Cafe)
class CafeAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'address', 'phone')
    search_fields = ('name', 'location')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('cafe', 'user', 'rating', 'created_at')
    list_filter = ('cafe', 'rating')
    search_fields = ('comment',)

@admin.register(CafeStat)
class CafeStatAdmin(admin.ModelAdmin):
    list_display = ('cafe', 'date', 'views')
    list_filter = ('cafe', 'date')