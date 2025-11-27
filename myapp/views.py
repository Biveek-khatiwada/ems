from django.http import HttpResponse
from django.shortcuts import render
import datetime
from emp.models import CustomUser

def home_page(request):
    try:
        
        emp_count = CustomUser.objects.count()
        emp_details = CustomUser.objects.all() 
        
        context = {
            'emp_details': emp_details,
            'emp_count': emp_count,
        }
        
        for i in emp_details:
            print(i.phone_number)
        return render(request, 'emp/home.html', context)
    
    except Exception as e:
        print(f"Error in home_page: {e}")
        return render(request, 'emp/home.html', {'emp_details': [], 'emp_count': 0})