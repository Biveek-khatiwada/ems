from django.http import HttpResponse
from django.shortcuts import render
import datetime

def home_page(request):
    return render(request,'emp/home.html')