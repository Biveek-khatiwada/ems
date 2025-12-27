from django.contrib import admin
from django.urls import path,include
from . import views
app_name = "emp"
urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('add-employee/', views.add_employee, name='add_employee'),
]


