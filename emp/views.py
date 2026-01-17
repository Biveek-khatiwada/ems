from django.shortcuts import render, redirect
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
import datetime
from emp.models import CustomUser, Department
from emp.forms import CustomUserCreationForm
from django.http import JsonResponse
from django.contrib import messages


def home_page(request):
    try:
        # Get filter parameters
        department_filter = request.GET.get('department', '')
        role_filter = request.GET.get('role', '')
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('q', '')
        page_number = request.GET.get('page', 1)
        
        # Start with all employees
        emp_details = CustomUser.objects.select_related('user', 'department').order_by('-created_at')
        
        # Apply filters
        if department_filter:
            emp_details = emp_details.filter(department_id=department_filter)
        
        if role_filter:
            emp_details = emp_details.filter(role=role_filter)
        
        if status_filter:
            if status_filter == 'active':
                emp_details = emp_details.filter(is_active=True)
            elif status_filter == 'inactive':
                emp_details = emp_details.filter(is_active=False)
        
        if search_query:
            emp_details = emp_details.filter(
                Q(user__username__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(phone_number__icontains=search_query) |
                Q(department__name__icontains=search_query) |
                Q(address__icontains=search_query)
            )
        
        # Pagination
        paginator = Paginator(emp_details, 10)  # 10 items per page
        page_obj = paginator.get_page(page_number)
        
        # Calculate statistics
        total_employees = CustomUser.objects.count()
        active_employees = CustomUser.objects.filter(is_active=True).count()
        managers_count = CustomUser.objects.filter(role='manager').count()
        
        # Get departments - Use a different name for annotation
        departments = Department.objects.annotate(
            dept_employee_count=Count('employees')  # Changed from employee_count
        ).order_by('name')
        
        total_departments = departments.filter(is_active=True).count()
        
        # Calculate percentages
        active_percentage = round((active_employees / total_employees * 100) if total_employees > 0 else 0, 1)
        managers_percentage = round((managers_count / total_employees * 100) if total_employees > 0 else 0, 1)
        
        # Calculate new hires this month
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_hires_this_month = CustomUser.objects.filter(
            created_at__gte=current_month
        ).count()
        
        # Calculate average employees per department
        avg_employees_per_dept = round(total_employees / total_departments, 1) if total_departments > 0 else 0
        
        context = {
            'emp_details': page_obj,
            'emp_count': total_employees,
            'current_time': datetime.datetime.now(),
            'departments': departments,
            'total_employees': total_employees,
            'active_employees': active_employees,
            'managers_count': managers_count,
            'total_departments': total_departments,
            'active_percentage': active_percentage,
            'managers_percentage': managers_percentage,
            'new_hires_this_month': new_hires_this_month,
            'avg_employees_per_dept': avg_employees_per_dept,
            'selected_department': department_filter,
            'selected_role': role_filter,
            'selected_status': status_filter,
            'search_query': search_query,
            'page_obj': page_obj,
        }
        
        return render(request, 'emp/home.html', context)
    
    except Exception as e:
        print(f"Error in home_page: {e}")
        context = {
            'emp_details': [],
            'emp_count': 0,
            'current_time': datetime.datetime.now(),
            'departments': Department.objects.all(),
            'total_employees': 0,
            'active_employees': 0,
            'managers_count': 0,
            'total_departments': 0,
            'active_percentage': 0,
            'managers_percentage': 0,
            'new_hires_this_month': 0,
            'avg_employees_per_dept': 0,
            'page_obj': None,
        }
        return render(request, 'emp/home.html', context)
    
def add_employee(request):
    """
    Handle AJAX request to add a new employee
    """
    if request.method == 'POST':
        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            try:
                # Save the employee
                employee = form.save()
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': f'Employee "{employee.full_name}" added successfully!',
                        'employee': {
                            'id': str(employee.id),
                            'name': employee.full_name,
                            'username': employee.username,
                            'email': employee.email,
                            'phone': str(employee.phone_number),
                            'department': employee.department.name if employee.department else 'No Department',
                            'role': employee.get_role_display(),
                            'status': 'Active' if employee.is_active else 'Inactive',
                            'created_at': employee.created_at.strftime('%b %d, %Y'),
                            'avatar_url': f'https://ui-avatars.com/api/?name={employee.full_name}&background=random&size=45'
                        }
                    })
                else:
                    messages.success(request, f'Employee "{employee.full_name}" added successfully!')
                    return redirect('home_page')
                    
            except Exception as e:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'errors': {'__all__': [str(e)]}
                    }, status=400)
                else:
                    messages.error(request, f'Error adding employee: {str(e)}')
                    return redirect('home_page')
        else:
            
            if is_ajax:
            
                errors = {}
                for field in form.errors:
                    errors[field] = form.errors[field]
                return JsonResponse({
                    'success': False,
                    'errors': errors
                }, status=400)
            else:
            
                messages.error(request, 'Please correct the errors below.')
            
                return redirect('home_page')
    
    elif request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        
        form = CustomUserCreationForm()
        form_html = render(request, 'emp/partials/employee_form.html', {'form': form}).content.decode()
        return JsonResponse({'form_html': form_html})
    
    
    return redirect('home_page')

def manage_departments(request):
    """ View to manage departments"""
    departments = Department.objects.all().order_by('name')
    managers = CustomUser.objects.filter(role__in=['manager', 'admin'], is_active=True)
    
    return render(request, 'emp/manage_department.html', {
        'departments': departments,
        'managers': managers
    })
    
def add_department(request):
    """ Add new department via AJAX """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            name = request.POST.get('name')
            code = request.POST.get('code')
            description = request.POST.get('description', '')
            manager_id = request.POST.get('manager')
            is_active = request.POST.get('is_active') == 'on'
            
            
            if not name or not code:
                return JsonResponse({
                    'success': False,
                    'errors': {
                        'name': ['Department name is required'] if not name else [],
                        'code': ['Department code is required'] if not code else []
                    }
                })
            
            
            if Department.objects.filter(name=name).exists():
                return JsonResponse({
                    'success': False,
                    'errors': {'name': ['A department with this name already exists.']}
                })
            
            if Department.objects.filter(code=code).exists():
                return JsonResponse({
                    'success': False,
                    'errors': {'code': ['A department with this code already exists.']}
                })
            
            
            department = Department(
                name=name,
                code=code,
                description=description,
                is_active=is_active
            )
            
            
            if manager_id:
                try:
                    manager = CustomUser.objects.get(id=manager_id)
                    department.manager = manager
                except CustomUser.DoesNotExist:
                    pass
            
            department.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Department "{name}" added successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': {'__all__': [str(e)]}
            })
    
    return JsonResponse({'success': False, 'errors': {'__all__': ['Invalid request']}})