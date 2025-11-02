"""
Configuracion del Django Admin para la app de cuentas
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html

admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuracion del admin para el modelo User
    Extiende el UserAdmin por defecto de Django con funcionalidades adicionales
    """
    list_display = [
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
        'date_joined',
        'last_login_display'
    ]
    
    list_filter = [
        'is_staff',
        'is_superuser',
        'is_active',
        'date_joined',
        'last_login'
    ]
    
    search_fields = [
        'username',
        'first_name',
        'last_name',
        'email'
    ]
    
    ordering = ['-date_joined']
    
    date_hierarchy = 'date_joined'
    
    # Fieldsets para la pagina de edicion
    fieldsets = (
        ('Login Info', {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # Fieldsets para la pagina de creacion
    add_fieldsets = (
        ('Login Info', {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
    )
    
    def last_login_display(self, obj):
        """Muestra el ultimo login de forma mas legible"""
        if obj.last_login:
            return obj.last_login.strftime('%Y-%m-%d %H:%M')
        return 'Never'
    last_login_display.short_description = 'Last Login'
    last_login_display.admin_order_field = 'last_login'
