from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('dashboard/',views.employee_dashboard, name="employee_dashboard"),
]


