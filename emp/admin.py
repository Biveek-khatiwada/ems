from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    CustomUser, Department, 
    Attendance, LeaveRequest, AttendanceSettings
)
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import models

# Inline admin for CustomUser in User admin
class CustomUserInline(admin.StackedInline):
    model = CustomUser
    can_delete = False
    verbose_name_plural = 'Employee Profile'
    fields = ('phone_number', 'address', 'department', 'role', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    fk_name = 'user'

# Customize the User admin to include CustomUser
class UserAdmin(BaseUserAdmin):
    inlines = (CustomUserInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_department', 'get_role', 'is_staff', 'is_active')
    list_filter = ('custom_user_profile__department', 'custom_user_profile__role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'custom_user_profile__phone_number')
    
    def get_department(self, obj):
        if hasattr(obj, 'custom_user_profile') and obj.custom_user_profile.department:
            return obj.custom_user_profile.department.name
        return "No Department"
    get_department.short_description = 'Department'
    get_department.admin_order_field = 'custom_user_profile__department__name'
    
    def get_role(self, obj):
        if hasattr(obj, 'custom_user_profile'):
            return obj.custom_user_profile.get_role_display()
        return "No Role"
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'custom_user_profile__role'

# Department Admin
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'manager_name', 'employee_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description', 'manager__user__username')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at', 'employee_count')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Management', {
            'fields': ('manager',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def manager_name(self, obj):
        if obj.manager:
            return obj.manager.user.get_full_name() or obj.manager.user.username
        return "No Manager"
    manager_name.short_description = 'Manager'
    
    def employee_count(self, obj):
        return obj.employees.count()
    employee_count.short_description = 'Employees'

# Attendance Admin
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee_name', 'department', 'date', 'status_badge', 'check_in', 'check_out', 
                    'total_hours', 'late_status', 'marked_by_name', 'marked_at')
    list_filter = ('status', 'date', 'department', ('check_in', admin.EmptyFieldListFilter))
    search_fields = ('employee__user__username', 'employee__user__first_name', 
                     'employee__user__last_name', 'employee__department__name', 'notes')
    date_hierarchy = 'date'
    readonly_fields = ('marked_at', 'total_hours')
    list_per_page = 50
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'department', 'date')
        }),
        ('Attendance Details', {
            'fields': ('status', 'check_in', 'check_out', 'total_hours')
        }),
        ('Additional Information', {
            'fields': ('notes', 'marked_by', 'marked_at'),
            'classes': ('collapse',)
        }),
    )
    
    def employee_name(self, obj):
        url = reverse('admin:emp_customuser_change', args=[obj.employee.id])
        name = obj.employee.user.get_full_name() or obj.employee.user.username
        return format_html('<a href="{}">{}</a>', url, name)
    employee_name.short_description = 'Employee'
    employee_name.admin_order_field = 'employee__user__first_name'
    
    def department(self, obj):
        if obj.department:
            return obj.department.name
        return "No Department"
    department.short_description = 'Department'
    
    def status_badge(self, obj):
        colors = {
            'present': 'green',
            'absent': 'red',
            'late': 'orange',
            'leave': 'blue',
            'half_day': 'purple',
            'holiday': 'gray',
            'weekend': 'darkgray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def late_status(self, obj):
        if obj.status == 'present' and obj.check_in:
            # Check if check-in is after 9:30 AM (example)
            check_in_time = datetime.combine(obj.date, obj.check_in)
            late_threshold = datetime.combine(obj.date, datetime.strptime('09:30', '%H:%M').time())
            if check_in_time > late_threshold:
                delay_minutes = int((check_in_time - late_threshold).total_seconds() / 60)
                return format_html(
                    '<span style="color: orange; font-weight: bold;">{} min late</span>',
                    delay_minutes
                )
        return "-"
    late_status.short_description = 'Late Status'
    
    def marked_by_name(self, obj):
        if obj.marked_by:
            return obj.marked_by.get_full_name() or obj.marked_by.username
        return "System"
    marked_by_name.short_description = 'Marked By'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Prefetch related objects for better performance
        return qs.select_related('employee__user', 'department', 'marked_by')
    
    # Custom actions
    actions = ['mark_as_present', 'mark_as_absent', 'mark_as_leave']
    
    def mark_as_present(self, request, queryset):
        updated = queryset.update(status='present', marked_by=request.user, marked_at=timezone.now())
        self.message_user(request, f'{updated} attendance records marked as Present.')
    mark_as_present.short_description = "Mark selected as Present"
    
    def mark_as_absent(self, request, queryset):
        updated = queryset.update(status='absent', check_in=None, check_out=None, total_hours=0, 
                                  marked_by=request.user, marked_at=timezone.now())
        self.message_user(request, f'{updated} attendance records marked as Absent.')
    mark_as_absent.short_description = "Mark selected as Absent"
    
    def mark_as_leave(self, request, queryset):
        updated = queryset.update(status='leave', check_in=None, check_out=None, total_hours=0,
                                  marked_by=request.user, marked_at=timezone.now())
        self.message_user(request, f'{updated} attendance records marked as On Leave.')
    mark_as_leave.short_description = "Mark selected as On Leave"

# Leave Request Admin
@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee_name', 'leave_type_badge', 'date_range', 'total_days', 
                    'status_badge', 'reviewed_by_name', 'created_at')
    list_filter = ('status', 'leave_type', 'start_date', 'created_at')
    search_fields = ('employee__user__username', 'employee__user__first_name', 
                     'employee__user__last_name', 'reason', 'response_notes')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at', 'total_days', 'reviewed_at')
    list_per_page = 50
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee',)
        }),
        ('Leave Details', {
            'fields': ('leave_type', 'start_date', 'end_date', 'total_days', 'reason')
        }),
        ('Supporting Documents', {
            'fields': ('supporting_docs',),
            'classes': ('collapse',)
        }),
        ('Review Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'response_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def employee_name(self, obj):
        url = reverse('admin:emp_customuser_change', args=[obj.employee.id])
        name = obj.employee.user.get_full_name() or obj.employee.user.username
        return format_html('<a href="{}">{}</a>', url, name)
    employee_name.short_description = 'Employee'
    
    def leave_type_badge(self, obj):
        colors = {
            'sick': 'red',
            'casual': 'blue',
            'earned': 'green',
            'maternity': 'purple',
            'paternity': 'lightblue',
            'unpaid': 'gray',
        }
        color = colors.get(obj.leave_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.get_leave_type_display()
        )
    leave_type_badge.short_description = 'Leave Type'
    
    def date_range(self, obj):
        return format_html(
            '{} - {}<br><small style="color: gray;">{} days</small>',
            obj.start_date.strftime('%b %d'),
            obj.end_date.strftime('%b %d, %Y'),
            obj.total_days
        )
    date_range.short_description = 'Date Range'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name() or obj.reviewed_by.username
        return "Pending"
    reviewed_by_name.short_description = 'Reviewed By'
    
    # Custom actions
    actions = ['approve_leave', 'reject_leave']
    
    def approve_leave(self, request, queryset):
        updated = queryset.update(status='approved', reviewed_by=request.user, 
                                  reviewed_at=timezone.now())
        self.message_user(request, f'{updated} leave requests approved.')
    approve_leave.short_description = "Approve selected leave requests"
    
    def reject_leave(self, request, queryset):
        updated = queryset.update(status='rejected', reviewed_by=request.user, 
                                  reviewed_at=timezone.now())
        self.message_user(request, f'{updated} leave requests rejected.')
    reject_leave.short_description = "Reject selected leave requests"
    
    # Inline actions in list view
    def response_actions(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<div style="display: flex; gap: 5px;">'
                '<a href="{}" class="button" style="background-color: green; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none;">Approve</a>'
                '<a href="{}" class="button" style="background-color: red; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none;">Reject</a>'
                '</div>',
                reverse('admin:approve_leave', args=[obj.id]),
                reverse('admin:reject_leave', args=[obj.id])
            )
        return "-"

# Attendance Settings Admin
@admin.register(AttendanceSettings)
class AttendanceSettingsAdmin(admin.ModelAdmin):
    list_display = ('department', 'working_hours', 'late_threshold', 'half_day_threshold', 
                    'check_in_range', 'check_out_range', 'created_by_name')
    list_filter = ('department',)
    search_fields = ('department__name', 'department__code')
    readonly_fields = ('created_by', 'holidays_preview')
    
    fieldsets = (
        ('Department', {
            'fields': ('department',)
        }),
        ('Working Hours', {
            'fields': ('working_hours',)
        }),
        ('Time Thresholds', {
            'fields': ('late_threshold', 'half_day_threshold')
        }),
        ('Check-in/Check-out Windows', {
            'fields': ('check_in_start', 'check_in_end', 'check_out_start', 'check_out_end')
        }),
        ('Weekdays & Holidays', {
            'fields': ('weekdays', 'holidays', 'holidays_preview')
        }),
        ('Created By', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def check_in_range(self, obj):
        return f"{obj.check_in_start.strftime('%H:%M')} - {obj.check_in_end.strftime('%H:%M')}"
    check_in_range.short_description = 'Check-in Window'
    
    def check_out_range(self, obj):
        return f"{obj.check_out_start.strftime('%H:%M')} - {obj.check_out_end.strftime('%H:%M')}"
    check_out_range.short_description = 'Check-out Window'
    
    def created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return "System"
    created_by_name.short_description = 'Created By'
    
    def holidays_preview(self, obj):
        if obj.holidays and len(obj.holidays) > 0:
            holiday_list = "<br>".join(obj.holidays[:5])  # Show first 5 holidays
            if len(obj.holidays) > 5:
                holiday_list += f"<br><em>... and {len(obj.holidays) - 5} more</em>"
            return format_html(holiday_list)
        return "No holidays configured"
    holidays_preview.short_description = 'Holidays Preview'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # If creating new
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# CustomUser Admin (standalone)
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'phone_number', 'department_name', 'role_badge', 
                    'is_active_badge', 'created_at', 'attendance_summary')
    list_filter = ('role', 'is_active', 'department', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 
                     'user__last_name', 'phone_number', 'address')
    readonly_fields = ('created_at', 'updated_at', 'attendance_stats')
    list_per_page = 50
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Employee Details', {
            'fields': ('phone_number', 'address', 'profile_picture')
        }),
        ('Department & Role', {
            'fields': ('department', 'role')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Attendance Statistics', {
            'fields': ('attendance_stats',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_name(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        name = obj.user.get_full_name() or obj.user.username
        return format_html('<a href="{}">{}</a>', url, name)
    user_name.short_description = 'Employee'
    user_name.admin_order_field = 'user__first_name'
    
    def department_name(self, obj):
        if obj.department:
            url = reverse('admin:emp_department_change', args=[obj.department.id])
            return format_html('<a href="{}">{}</a>', url, obj.department.name)
        return "No Department"
    department_name.short_description = 'Department'
    
    def role_badge(self, obj):
        colors = {
            'admin': 'purple',
            'manager': 'blue',
            'employee': 'green',
        }
        color = colors.get(obj.role, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = 'Role'
    
    def is_active_badge(self, obj):
        color = 'green' if obj.is_active else 'red'
        text = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, text
        )
    is_active_badge.short_description = 'Status'
    
    def attendance_summary(self, obj):
        # Calculate attendance stats for the current month
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        
        present_count = Attendance.objects.filter(
            employee=obj,
            date__gte=start_of_month,
            date__lte=today,
            status='present'
        ).count()
        
        total_days = (today - start_of_month).days + 1
        attendance_rate = round((present_count / total_days) * 100) if total_days > 0 else 0
        
        return format_html(
            '{}%<br><small style="color: gray;">{}/{} days</small>',
            attendance_rate, present_count, total_days
        )
    attendance_summary.short_description = 'This Month'
    
    def attendance_stats(self, obj):
        # Detailed attendance statistics
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        
        stats = Attendance.objects.filter(
            employee=obj,
            date__gte=last_30_days,
            date__lte=today
        ).values('status').annotate(count=models.Count('id'))
        
        stat_dict = {stat['status']: stat['count'] for stat in stats}
        
        html = '<h4>Last 30 Days Attendance</h4>'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr><th>Status</th><th>Count</th></tr>'
        
        for status, display in Attendance.ATTENDANCE_STATUS:
            count = stat_dict.get(status, 0)
            html += f'<tr><td>{display}</td><td>{count}</td></tr>'
        
        html += '</table>'
        return format_html(html)
    attendance_stats.short_description = 'Attendance Statistics'
    
    # Custom actions
    actions = ['activate_users', 'deactivate_users', 'make_manager', 'make_employee']
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} employees activated.')
    activate_users.short_description = "Activate selected employees"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} employees deactivated.')
    deactivate_users.short_description = "Deactivate selected employees"
    
    def make_manager(self, request, queryset):
        updated = queryset.update(role='manager')
        self.message_user(request, f'{updated} employees promoted to Manager.')
    make_manager.short_description = "Promote to Manager"
    
    def make_employee(self, request, queryset):
        updated = queryset.update(role='employee')
        self.message_user(request, f'{updated} managers demoted to Employee.')
    make_employee.short_description = "Demote to Employee"

# Register custom admin views
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Optional: Custom admin site title and header
admin.site.site_title = "Employee Management System"
admin.site.site_header = "Employee Management System Administration"
admin.site.index_title = "Dashboard"