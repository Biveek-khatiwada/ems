from django.contrib import admin
from django.urls import path,include
from . import views
app_name = "emp"
urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('add-employee/', views.add_employee, name='add_employee'),
    path('manage-departments/', views.manage_departments, name='manage_departments'),
    path('departments/get/<int:department_id>/', views.get_department_data, name='get_department_data'),
    path('departments/add/', views.add_department, name='add_department'),
    path('departments/edit/<int:department_id>/', views.edit_department, name='edit_department'),
    path('departments/delete/<int:department_id>/', views.delete_department, name='delete_department'),
]


