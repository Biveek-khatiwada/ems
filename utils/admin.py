from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import ActivityLog, AuditLog, SystemLog, LoginLog
from django.db.models import Count
import json

# Common admin configuration
class BaseLogAdmin(admin.ModelAdmin):
    list_per_page = 50
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    list_filter = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')
    
    def has_add_permission(self, request):
        # Prevent adding logs manually through admin
        return False
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing logs
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Allow deletion only for superusers
        return request.user.is_superuser

@admin.register(ActivityLog)
class ActivityLogAdmin(BaseLogAdmin):
    list_display = [
        'id_short', 'user_display', 'log_type_display', 
        'module_display', 'action_short', 'status_display', 
        'ip_address', 'created_at_display'
    ]
    list_filter = [
        'log_type', 'module', 'status', 'created_at', 'user'
    ]
    search_fields = [
        'action', 'user__username', 'user__email', 
        'user__first_name', 'user__last_name', 'ip_address'
    ]
    readonly_fields = [
        'user', 'log_type', 'module', 'action', 
        'ip_address', 'user_agent', 'status', 
        'additional_data_display', 'created_at'
    ]
    
    fieldsets = (
        ('Log Information', {
            'fields': ('id', 'created_at')
        }),
        ('User Information', {
            'fields': ('user_display', 'ip_address', 'user_agent')
        }),
        ('Activity Details', {
            'fields': ('log_type', 'module', 'action', 'status')
        }),
        ('Additional Data', {
            'fields': ('additional_data_display',),
            'classes': ('collapse',)
        }),
    )
    
    def id_short(self, obj):
        return str(obj.id)[:8] + "..."
    id_short.short_description = "ID"
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.username})"
        return "System"
    user_display.short_description = "User"
    
    def log_type_display(self, obj):
        colors = {
            'login': 'green',
            'logout': 'blue',
            'create': 'teal',
            'update': 'orange',
            'delete': 'red',
            'view': 'purple',
            'export': 'cyan',
            'import': 'indigo',
            'system': 'gray',
            'error': 'darkred',
        }
        color = colors.get(obj.log_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_log_type_display()
        )
    log_type_display.short_description = "Type"
    
    def module_display(self, obj):
        return obj.get_module_display()
    module_display.short_description = "Module"
    
    def action_short(self, obj):
        if len(obj.action) > 60:
            return obj.action[:57] + "..."
        return obj.action
    action_short.short_description = "Action"
    
    def status_display(self, obj):
        colors = {
            'success': 'green',
            'failed': 'red',
            'warning': 'orange',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = "Status"
    
    def created_at_display(self, obj):
        return timezone.localtime(obj.created_at).strftime('%Y-%m-%d %H:%M:%S')
    created_at_display.short_description = "Created At"
    
    def additional_data_display(self, obj):
        if obj.additional_data:
            pretty_json = json.dumps(obj.additional_data, indent=2, ensure_ascii=False)
            return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{}</pre>', pretty_json)
        return "No additional data"
    additional_data_display.short_description = "Additional Data"

@admin.register(AuditLog)
class AuditLogAdmin(BaseLogAdmin):
    list_display = [
        'id_short', 'user_display', 'action_display', 
        'model_name', 'object_repr_short', 'created_at_display'
    ]
    list_filter = [
        'action', 'model_name', 'created_at', 'user'
    ]
    search_fields = [
        'model_name', 'object_id', 'object_repr',
        'user__username', 'user__email', 'ip_address'
    ]
    readonly_fields = [
        'user', 'action', 'model_name', 'object_id',
        'object_repr', 'changes_display', 'ip_address', 'created_at'
    ]
    
    fieldsets = (
        ('Log Information', {
            'fields': ('id', 'created_at')
        }),
        ('User Information', {
            'fields': ('user_display', 'ip_address')
        }),
        ('Object Information', {
            'fields': ('model_name', 'object_id', 'object_repr')
        }),
        ('Action Details', {
            'fields': ('action',)
        }),
        ('Changes', {
            'fields': ('changes_display',),
            'classes': ('collapse',)
        }),
    )
    
    def id_short(self, obj):
        return str(obj.id)[:8] + "..."
    id_short.short_description = "ID"
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.username})"
        return "System"
    user_display.short_description = "User"
    
    def action_display(self, obj):
        colors = {
            'CREATE': 'green',
            'UPDATE': 'orange',
            'DELETE': 'red',
            'SOFT_DELETE': 'darkorange',
            'RESTORE': 'blue',
        }
        color = colors.get(obj.action, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_action_display()
        )
    action_display.short_description = "Action"
    
    def object_repr_short(self, obj):
        if len(obj.object_repr) > 50:
            return obj.object_repr[:47] + "..."
        return obj.object_repr
    object_repr_short.short_description = "Object"
    
    def created_at_display(self, obj):
        return timezone.localtime(obj.created_at).strftime('%Y-%m-%d %H:%M:%S')
    created_at_display.short_description = "Created At"
    
    def changes_display(self, obj):
        if obj.changes:
            pretty_json = json.dumps(obj.changes, indent=2, ensure_ascii=False)
            return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{}</pre>', pretty_json)
        return "No changes recorded"
    changes_display.short_description = "Changes"

@admin.register(SystemLog)
class SystemLogAdmin(BaseLogAdmin):
    list_display = [
        'id_short', 'level_display', 'source', 
        'message_short', 'created_at_display'
    ]
    list_filter = [
        'level', 'source', 'created_at'
    ]
    search_fields = [
        'source', 'message', 'traceback'
    ]
    readonly_fields = [
        'level', 'source', 'message', 'traceback_display',
        'additional_data_display', 'created_at'
    ]
    
    fieldsets = (
        ('Log Information', {
            'fields': ('id', 'created_at')
        }),
        ('Log Details', {
            'fields': ('level', 'source', 'message')
        }),
        ('Traceback', {
            'fields': ('traceback_display',),
            'classes': ('collapse',)
        }),
        ('Additional Data', {
            'fields': ('additional_data_display',),
            'classes': ('collapse',)
        }),
    )
    
    def id_short(self, obj):
        return str(obj.id)[:8] + "..."
    id_short.short_description = "ID"
    
    def level_display(self, obj):
        colors = {
            'DEBUG': 'gray',
            'INFO': 'blue',
            'WARNING': 'orange',
            'ERROR': 'red',
            'CRITICAL': 'darkred',
        }
        color = colors.get(obj.level, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_level_display()
        )
    level_display.short_description = "Level"
    
    def message_short(self, obj):
        if len(obj.message) > 80:
            return obj.message[:77] + "..."
        return obj.message
    message_short.short_description = "Message"
    
    def created_at_display(self, obj):
        return timezone.localtime(obj.created_at).strftime('%Y-%m-%d %H:%M:%S')
    created_at_display.short_description = "Created At"
    
    def traceback_display(self, obj):
        if obj.traceback:
            return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; white-space: pre-wrap;">{}</pre>', obj.traceback)
        return "No traceback"
    traceback_display.short_description = "Traceback"
    
    def additional_data_display(self, obj):
        if obj.additional_data:
            pretty_json = json.dumps(obj.additional_data, indent=2, ensure_ascii=False)
            return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{}</pre>', pretty_json)
        return "No additional data"
    additional_data_display.short_description = "Additional Data"

@admin.register(LoginLog)
class LoginLogAdmin(BaseLogAdmin):
    list_display = [
        'id_short', 'username', 'user_display', 
        'status_display', 'ip_address', 'created_at_display'
    ]
    list_filter = [
        'status', 'created_at', 'user'
    ]
    search_fields = [
        'username', 'user__username', 'user__email',
        'ip_address', 'failure_reason'
    ]
    readonly_fields = [
        'username', 'user', 'status', 'ip_address',
        'user_agent', 'failure_reason', 'created_at'
    ]
    
    fieldsets = (
        ('Log Information', {
            'fields': ('id', 'created_at')
        }),
        ('User Information', {
            'fields': ('username', 'user_display', 'ip_address', 'user_agent')
        }),
        ('Login Details', {
            'fields': ('status', 'failure_reason')
        }),
    )
    
    def id_short(self, obj):
        return str(obj.id)[:8] + "..."
    id_short.short_description = "ID"
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.username})"
        return "N/A"
    user_display.short_description = "User"
    
    def status_display(self, obj):
        colors = {
            'success': 'green',
            'failed': 'red',
            'locked': 'darkred',
            'expired': 'orange',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = "Status"
    
    def created_at_display(self, obj):
        return timezone.localtime(obj.created_at).strftime('%Y-%m-%d %H:%M:%S')
    created_at_display.short_description = "Created At"

# Optional: Dashboard view for logs
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.urls import path

class LogDashboardView(TemplateView):
    template_name = 'admin/logs_dashboard.html'
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get recent logs
        context['recent_activities'] = ActivityLog.objects.all()[:10]
        context['recent_audits'] = AuditLog.objects.all()[:10]
        context['recent_system_logs'] = SystemLog.objects.filter(level__in=['ERROR', 'WARNING'])[:10]
        context['recent_login_attempts'] = LoginLog.objects.all()[:10]
        
        # Get statistics
        context['activity_stats'] = ActivityLog.objects.values('log_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        context['login_stats'] = LoginLog.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        context['system_log_stats'] = SystemLog.objects.values('level').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Today's stats
        today = timezone.now().date()
        context['today_activities'] = ActivityLog.objects.filter(
            created_at__date=today
        ).count()
        
        context['today_logins'] = LoginLog.objects.filter(
            created_at__date=today, status='success'
        ).count()
        
        context['today_errors'] = SystemLog.objects.filter(
            created_at__date=today, level='ERROR'
        ).count()
        
        return context

# Add custom admin site with dashboard
class CustomAdminSite(admin.AdminSite):
    site_header = "Employee Management System - Admin"
    site_title = "EMS Admin"
    index_title = "Dashboard"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('logs-dashboard/', self.admin_view(LogDashboardView.as_view()), name='logs-dashboard'),
        ]
        return custom_urls + urls
    
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        
        # Add custom dashboard to the app list
        app_list.insert(0, {
            'name': 'Logs Dashboard',
            'app_label': 'logs_dashboard',
            'app_url': '/admin/logs-dashboard/',
            'has_module_perms': True,
            'models': [
                {
                    'name': 'Dashboard',
                    'object_name': 'dashboard',
                    'admin_url': '/admin/logs-dashboard/',
                    'view_only': True,
                }
            ],
        })
        
        return app_list

# Create a templates folder in your app and add:
# templates/admin/logs_dashboard.html
"""
{% extends "admin/base_site.html" %}
{% load i18n static %}

{% block extrastyle %}
{{ block.super }}
<style>
.dashboard-card {
    background: white;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}
.stat-card {
    background: white;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.stat-number {
    font-size: 2.5rem;
    font-weight: bold;
    color: #4361ee;
}
.stat-label {
    color: #666;
    margin-top: 10px;
}
.log-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}
.log-table th, .log-table td {
    padding: 10px;
    text-align: left;
    border-bottom: 1px solid #eee;
}
.log-table th {
    background: #f8f9fa;
    font-weight: 600;
}
</style>
{% endblock %}

{% block content %}
<h1>{% trans "Logs Dashboard" %}</h1>

<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-number">{{ today_activities }}</div>
        <div class="stat-label">Today's Activities</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ today_logins }}</div>
        <div class="stat-label">Today's Logins</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ today_errors }}</div>
        <div class="stat-label">Today's Errors</div>
    </div>
</div>

<div class="dashboard-card">
    <h2>Recent Activities</h2>
    <table class="log-table">
        <thead>
            <tr>
                <th>User</th>
                <th>Type</th>
                <th>Module</th>
                <th>Action</th>
                <th>Time</th>
            </tr>
        </thead>
        <tbody>
            {% for log in recent_activities %}
            <tr>
                <td>{{ log.user_display|safe }}</td>
                <td>{{ log.log_type_display|safe }}</td>
                <td>{{ log.module_display }}</td>
                <td>{{ log.action_short }}</td>
                <td>{{ log.created_at|date:"H:i" }}</td>
            </tr>
            {% empty %}
            <tr><td colspan="5">No recent activities</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<div class="dashboard-card">
    <h2>Recent System Errors/Warnings</h2>
    <table class="log-table">
        <thead>
            <tr>
                <th>Level</th>
                <th>Source</th>
                <th>Message</th>
                <th>Time</th>
            </tr>
        </thead>
        <tbody>
            {% for log in recent_system_logs %}
            <tr>
                <td>{{ log.level_display|safe }}</td>
                <td>{{ log.source }}</td>
                <td>{{ log.message_short }}</td>
                <td>{{ log.created_at|date:"H:i" }}</td>
            </tr>
            {% empty %}
            <tr><td colspan="4">No recent system logs</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<div class="dashboard-card">
    <h2>Activity Statistics</h2>
    <table class="log-table">
        <thead>
            <tr>
                <th>Activity Type</th>
                <th>Count</th>
            </tr>
        </thead>
        <tbody>
            {% for stat in activity_stats %}
            <tr>
                <td>{{ stat.log_type }}</td>
                <td>{{ stat.count }}</td>
            </tr>
            {% empty %}
            <tr><td colspan="2">No statistics available</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
"""

# To use the custom admin site, in your project's urls.py:
# from django.contrib import admin
# from your_app.admin import CustomAdminSite
# 
# admin.site = CustomAdminSite()
# 
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     # ... other URLs
# ]