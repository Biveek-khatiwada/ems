from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

class CustomUserInline(admin.StackedInline):
    model = CustomUser
    can_delete = False
    verbose_name_plural = "Custom User Profile"
    fields = ('phone_number', 'department', 'address', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

class CustomUserAdmin(UserAdmin):
    inlines = (CustomUserInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_department', 'get_phone_number', 'is_staff')
    list_select_related = ('custom_user',)

    def get_department(self, instance):
        if hasattr(instance, 'custom_user'):
            return instance.custom_user.department
        return "-"
    get_department.short_description = "Department"

    def get_phone_number(self, instance):
        if hasattr(instance, 'custom_user'):
            return instance.custom_user.phone_number
        return "-"
    get_phone_number.short_description = "Phone Number"

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

@admin.register(CustomUser)
class CustomUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'department', 'created_at')
    list_filter = ('department', 'created_at')
    search_fields = ('user__username', 'phone_number', 'department', 'address')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('id', 'user')
        }),
        ("Profile Information", {
            'fields': ('phone_number', 'department', 'address')
        }),
        ("Timestamps", {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

# Unregister the default User admin and register with custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)