from django.http import HttpResponse
from django.shortcuts import render
import datetime
from emp.models import CustomUser
from django.db.models import Count

def home_page(request):
    try:
        emp_count = CustomUser.objects.count()
        emp_details = CustomUser.objects.select_related('user').all()
        
        context = {
            'emp_details': emp_details,
            'emp_count': emp_count,
            'current_time': datetime.datetime.now(),  # Add this line
        }
        
        return render(request, 'emp/home.html', context)
    
    except Exception as e:
        print(f"Error in home_page: {e}")
        context = {
            'emp_details': [],
            'emp_count': 0,
            'current_time': datetime.datetime.now(),  # Add this line for error case too
        }
        return render(request, 'emp/home.html', context)