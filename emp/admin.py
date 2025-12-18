from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Department, CustomUser


class CustomUserInline(admin.StackedInline):
    model = CustomUser
    can_delete = False
    verbose_name_plural = _("Employee Profile")
    fields = ('phone_number', 'department', 'role', 'address', 'is_active', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    fk_name = 'user'
    
    # Optional: Limit department choices to active departments
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "department":
            kwargs["queryset"] = Department.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CustomUserAdmin(UserAdmin):
    inlines = (CustomUserInline,)
    list_display = ('username', 'email', 'full_name', 'get_department', 'get_role', 'get_phone_number', 'is_active', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'custom_user_profile__department', 'custom_user_profile__role')
    list_select_related = ('custom_user_profile',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = _("Full Name")
    
    def get_department(self, obj):
        if hasattr(obj, 'custom_user_profile') and obj.custom_user_profile.department:
            return obj.custom_user_profile.department.name
        return "-"
    get_department.short_description = _("Department")
    get_department.admin_order_field = "custom_user_profile__department__name"
    
    def get_role(self, obj):
        if hasattr(obj, 'custom_user_profile'):
            return obj.custom_user_profile.get_role_display()
        return "-"
    get_role.short_description = _("Role")
    get_role.admin_order_field = "custom_user_profile__role"
    
    def get_phone_number(self, obj):
        if hasattr(obj, 'custom_user_profile'):
            return obj.custom_user_profile.phone_number
        return "-"
    get_phone_number.short_description = _("Phone Number")
    get_phone_number.admin_order_field = "custom_user_profile__phone_number"
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(CustomUser)
class CustomUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_info', 'phone_number', 'department_info', 'role', 'is_active', 'created_at')
    list_filter = ('department', 'role', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 
                     'phone_number', 'department__name', 'address')
    readonly_fields = ('id', 'created_at', 'updated_at', 'user_info_display')
    list_select_related = ('user', 'department')
    
    fieldsets = (
        (None, {
            'fields': ('id', 'user')
        }),
        (_("Profile Information"), {
            'fields': ('phone_number', 'department', 'role', 'address', 'is_active')
        }),
        (_("Timestamps"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_info(self, obj):
        return f"{obj.user.get_full_name() or obj.user.username} ({obj.user.email})"
    user_info.short_description = _("User")
    user_info.admin_order_field = "user__username"
    
    def user_info_display(self, obj):
        return f"{obj.user.get_full_name()} <{obj.user.email}>"
    user_info_display.short_description = _("User Details")
    
    def department_info(self, obj):
        if obj.department:
            return format_html(
                '<span style="font-weight:bold;">{}</span> (<code>{}</code>)',
                obj.department.name,
                obj.department.code
            )
        return "-"
    department_info.short_description = _("Department")
    department_info.admin_order_field = "department__name"


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'manager_info', 'employee_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description', 'manager__user__username', 'manager__user__first_name')
    readonly_fields = ('created_at', 'updated_at', 'employee_count_display')
    list_select_related = ('manager', 'manager__user')
    autocomplete_fields = ['manager']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'is_active')
        }),
        (_("Management"), {
            'fields': ('manager', 'description')
        }),
        (_("Statistics"), {
            'fields': ('employee_count_display',),
            'classes': ('collapse',)
        }),
        (_("Timestamps"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def manager_info(self, obj):
        if obj.manager:
            return obj.manager.user.get_full_name() or obj.manager.user.username
        return "-"
    manager_info.short_description = _("Manager")
    manager_info.admin_order_field = "manager__user__username"
    
    def employee_count_display(self, obj):
        return obj.employee_count
    employee_count_display.short_description = _("Number of Employees")
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('employees')


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)