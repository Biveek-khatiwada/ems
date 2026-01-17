from django.contrib import admin
from django.urls import path,include
from . import views
app_name = "emp"
urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('add-employee/', views.add_employee, name='add_employee'),
    path('manage-departments/',views.manage_departments,name='manage_departments'),
    path('departments/add/', views.add_department, name='add_department'),
]


