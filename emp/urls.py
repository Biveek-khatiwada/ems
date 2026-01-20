from django.contrib import admin
from django.urls import path,include
from . import views
app_name = "emp"
urlpatterns = [
    path('', views.home_page, name='home_page'),
    # employees 
    path('add-employee/', views.add_employee, name='add_employee'),
    path('edit-employee/<uuid:employee_id>/', views.edit_employee, name='edit_employee'),
    path('delete-employee/<uuid:employee_id>/', views.delete_employee, name='delete_employee'),
    path('toggle-status/<uuid:employee_id>/', views.toggle_employee_status, name='toggle_employee_status'),
    # departments
    path('manage-departments/', views.manage_departments, name='manage_departments'),
    path('departments/get/<int:department_id>/', views.get_department_data, name='get_department_data'),
    path('departments/add/', views.add_department, name='add_department'),
    path('departments/edit/<int:department_id>/', views.edit_department, name='edit_department'),
    path('departments/delete/<int:department_id>/', views.delete_department, name='delete_department'),
    #login
    path('login/', views.user_login, name='login'),
    path('logout/',views.user_logout, name='logout'),
    path('complete-profile/',views.complete_profile, name='complete_profile'),
    path('my-profile/',views.my_profile, name='my_profile'),
    
    path('attendance/', views.attendance_dashboard, name='attendance_dashboard'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/bulk-mark/', views.bulk_mark_attendance, name='bulk_mark_attendance'),
    path('attendance/report/', views.attendance_report, name='attendance_report'),
    path('attendance/report/<int:employee_id>/', views.attendance_report, name='employee_attendance_report'),
    path('attendance/leaves/', views.manage_leave_requests, name='manage_leaves'),
    path('attendance/settings/', views.attendance_settings, name='attendance_settings'),
    
    # API endpoints
    path('api/attendance/daily/', views.get_daily_attendance, name='api_daily_attendance'),
    path('api/attendance/employee/<int:employee_id>/', views.get_employee_attendance, name='api_employee_attendance'),
    path('api/attendance/monthly-summary/', views.monthly_attendance_summary, name='api_monthly_summary'),
]


