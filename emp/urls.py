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
    path('complete-profile/',views.user_profile, name='complete_profile'),
]


