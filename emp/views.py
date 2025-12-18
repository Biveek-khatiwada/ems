from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count, Q
from .models import CustomUser, Department
from django.utils import timezone

def employee_dashboard(request):
    # Get all employees
    employees = CustomUser.objects.select_related('user', 'department').order_by('-created_at')
    
    # Apply filters
    department_filter = request.GET.get('department')
    role_filter = request.GET.get('role')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('q', '')
    
    if department_filter:
        employees = employees.filter(department_id=department_filter)
    
    if role_filter:
        employees = employees.filter(role=role_filter)
    
    if status_filter:
        if status_filter == 'active':
            employees = employees.filter(is_active=True)
        elif status_filter == 'inactive':
            employees = employees.filter(is_active=False)
    
    if search_query:
        employees = employees.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(employees, 25)  # Show 25 employees per page
    
    try:
        emp_details = paginator.page(page)
    except PageNotAnInteger:
        emp_details = paginator.page(1)
    except EmptyPage:
        emp_details = paginator.page(paginator.num_pages)
    
    # Get page range for pagination
    page_range = paginator.get_elided_page_range(number=page, on_each_side=2, on_ends=1)
    
    # Get departments
    departments = Department.objects.annotate(
        employee_count=Count('employees')
    ).order_by('name')
    
    # Statistics
    total_employees = CustomUser.objects.count()
    active_employees = CustomUser.objects.filter(is_active=True).count()
    managers_count = CustomUser.objects.filter(role='manager').count()
    total_departments = Department.objects.filter(is_active=True).count()
    
    # Calculate percentages
    active_percentage = round((active_employees / total_employees * 100) if total_employees > 0 else 0, 1)
    managers_percentage = round((managers_count / total_employees * 100) if total_employees > 0 else 0, 1)
    
    # New hires this month
    from django.db.models.functions import TruncMonth
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_hires_this_month = CustomUser.objects.filter(
        created_at__gte=current_month
    ).count()
    
    
    avg_employees_per_dept = round(total_employees / total_departments, 1) if total_departments > 0 else 0
    
    context = {
        'emp_details': emp_details,
        'page_range': page_range,
        'departments': departments,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'managers_count': managers_count,
        'total_departments': total_departments,
        'active_percentage': active_percentage,
        'managers_percentage': managers_percentage,
        'new_hires_this_month': new_hires_this_month,
        'avg_employees_per_dept': avg_employees_per_dept,
        'current_time': timezone.now(),
        'selected_department': department_filter,
        'selected_role': role_filter,
        'selected_status': status_filter,
        'search_query': search_query,
    }
    print(context)
    return render(request, 'emp/dashboard.html', context)