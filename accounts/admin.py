from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'is_staff', 'is_owner']
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('age', 'avatar', 'is_owner')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {'fields': ('age', 'avatar', 'is_owner')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
