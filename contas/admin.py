from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ["nome"]
    list_display = ["nome", "email", "perfil", "is_active"]
    list_filter = ["perfil", "is_active"]
    search_fields = ["nome", "email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados", {"fields": ("nome", "perfil", "is_active")}),
        ("Permissões técnicas", {"fields": ("is_staff", "is_superuser")}),
        ("Datas", {"fields": ("last_login", "criado_em")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("nome", "email", "perfil", "password1", "password2")}),)
