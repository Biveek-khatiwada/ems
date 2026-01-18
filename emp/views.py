from django.shortcuts import render, redirect,get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
import datetime
from emp.models import CustomUser, Department
from emp.forms import CustomUserCreationForm
from django.http import JsonResponse
from django.contrib import messages
from emp.forms import DepartmentForm
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

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


@login_required
def edit_employee(request, employee_id):
    if request.method == 'POST':
        try:
            # Get the employee instance
            employee = CustomUser.objects.get(id=employee_id)
            user = employee.user
            
            # Get form data
            data = request.POST
            errors = {}
            
            # Validate email
            email = data.get('email', '').strip()
            if email:
                # Check if email is already taken by another user
                if User.objects.filter(email=email).exclude(id=user.id).exists():
                    errors['email'] = ['Email is already in use by another account.']
                else:
                    user.email = email
            
            # Update user fields
            user.first_name = data.get('first_name', '').strip()
            user.last_name = data.get('last_name', '').strip()
            
            # Update phone number (check uniqueness)
            phone_number = data.get('phone_number', '').strip()
            if phone_number:
                try:
                    phone_num = int(phone_number)
                    if CustomUser.objects.filter(phone_number=phone_num).exclude(id=employee_id).exists():
                        errors['phone_number'] = ['Phone number is already in use by another employee.']
                    else:
                        employee.phone_number = phone_num
                except ValueError:
                    errors['phone_number'] = ['Please enter a valid phone number.']
            
            # Update department
            department_id = data.get('department', '').strip()
            if department_id:
                try:
                    department = Department.objects.get(id=department_id)
                    employee.department = department
                except Department.DoesNotExist:
                    pass
            
            # Update address
            address = data.get('address', '').strip()
            if address:
                if len(address) > 100:
                    errors['address'] = ['Address must be 100 characters or less.']
                else:
                    employee.address = address
            
            # Update role
            role = data.get('role', 'employee')
            if role in ['employee', 'manager', 'admin']:
                employee.role = role
            
            # Update status
            employee.is_active = data.get('is_active') == 'on'
            
            # Update password if provided
            password1 = data.get('password1', '').strip()
            password2 = data.get('password2', '').strip()
            if password1 and password2:
                if password1 == password2:
                    user.set_password(password1)
                else:
                    errors['password1'] = ['Passwords do not match.']
            
            # If there are errors, return them
            if errors:
                return JsonResponse({
                    'success': False,
                    'errors': errors
                }, status=400)
            
            # Save changes
            user.save()
            employee.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Employee updated successfully!',
                'employee': {
                    'id': str(employee.id),
                    'name': user.get_full_name() or user.username,
                    'username': user.username,
                    'email': user.email,
                    'phone': str(employee.phone_number),
                    'department': employee.department.name if employee.department else 'No Department',
                    'role': employee.get_role_display(),
                    'status': 'Active' if employee.is_active else 'Inactive',
                    'avatar_url': f'https://ui-avatars.com/api/?name={user.get_full_name() or user.username}&background=4361ee&color=fff&size=45'
                }
            })
            
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': {'__all__': ['Employee not found.']}
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': {'__all__': [str(e)]}
            }, status=500)
    
    elif request.method == 'GET':
        
        try:
            employee = CustomUser.objects.get(id=employee_id)
            user = employee.user
            
            return JsonResponse({
                'success': True,
                'employee': {
                    'id': str(employee.id),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': str(employee.phone_number),
                    'department_id': str(employee.department.id) if employee.department else '',
                    'address': employee.address,
                    'role': employee.role,
                    'is_active': employee.is_active
                }
            })
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Employee not found'
            }, status=404)

@login_required
def delete_employee(request, employee_id):
    if request.method == 'POST':
        try:
            employee = CustomUser.objects.get(id=employee_id)
            user = employee.user
            
            # Get employee name for the message
            employee_name = user.get_full_name() or user.username
            
            # Delete the employee
            employee.delete()
            user.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Employee "{employee_name}" deleted successfully!'
            })
            
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Employee not found'
            }, status=404)

@login_required
def toggle_employee_status(request, employee_id):
    if request.method == 'POST':
        try:
            employee = CustomUser.objects.get(id=employee_id)
            
            # Toggle the status
            employee.is_active = not employee.is_active
            employee.save()
            
            action = "activated" if employee.is_active else "deactivated"
            
            return JsonResponse({
                'success': True,
                'message': f'Employee {action} successfully!',
                'is_active': employee.is_active
            })
            
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Employee not found'
            }, status=404)
    
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




@login_required
def manage_departments(request):
    """View to manage departments"""
    departments = Department.objects.all().order_by('name')
    
    total_departments = departments.count()
    active_departments = departments.filter(is_active=True).count()
    departments_with_managers = departments.exclude(manager__isnull=True).count()
    

    total_employees = 0
    for dept in departments:
        total_employees += dept.employee_count
    
    
    managers = CustomUser.objects.filter(
        role__in=['manager', 'admin'], 
        is_active=True
    ).select_related('user').order_by('user__first_name', 'user__last_name')
    
    return render(request, 'emp/manage_department.html', {
        'departments': departments,
        'managers': managers,
        'total_departments': total_departments,
        'active_departments': active_departments,
        'departments_with_managers': departments_with_managers,
        'total_employees': total_employees,
    })
    
@login_required
def get_department_data(request, department_id):
    """Get department data for editing via AJAX"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            department = get_object_or_404(Department, id=department_id)
            
            data = {
                'id': str(department.id),
                'name': department.name,
                'code': department.code,
                'description': department.description or '',
                'manager': str(department.manager.id) if department.manager else '',
                'is_active': department.is_active,
                'created_at': department.created_at.strftime('%Y-%m-%d'),
                'updated_at': department.updated_at.strftime('%Y-%m-%d'),
                'employee_count': department.employee_count,
                'active_employee_count': department.active_employee_count
            }
            
            return JsonResponse({
                'success': True,
                'department': data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
@require_http_methods(["POST"])
def add_department(request):
    """Add new department via AJAX"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            form = DepartmentForm(request.POST)
            
            if form.is_valid():
                department = form.save()
                
                # Get manager name
                manager_name = 'No Manager'
                if department.manager:
                    manager_name = department.manager.full_name or department.manager.username
                
                return JsonResponse({
                    'success': True,
                    'message': f'Department "{department.name}" added successfully!',
                    'department': {
                        'id': str(department.id),
                        'name': department.name,
                        'code': department.code,
                        'description': department.description or '',
                        'manager_name': manager_name,
                        'is_active': department.is_active,
                        'employee_count': 0,
                        'active_employee_count': 0,
                        'created_at': department.created_at.strftime('%b %d, %Y')
                    }
                })
            else:
                # Return form errors
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(e) for e in error_list]
                return JsonResponse({
                    'success': False,
                    'errors': errors
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': {'__all__': [str(e)]}
            }, status=500)
    
    return JsonResponse({'success': False, 'errors': {'__all__': ['Invalid request']}}, status=400)

@login_required
@require_http_methods(["POST"])
def edit_department(request, department_id):
    """Edit existing department via AJAX"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            department = get_object_or_404(Department, id=department_id)
            form = DepartmentForm(request.POST, instance=department)
            
            if form.is_valid():
                department = form.save()
                
                # Get manager name
                manager_name = 'No Manager'
                if department.manager:
                    manager_name = department.manager.full_name or department.manager.username
                
                return JsonResponse({
                    'success': True,
                    'message': f'Department "{department.name}" updated successfully!',
                    'department': {
                        'id': str(department.id),
                        'name': department.name,
                        'code': department.code,
                        'description': department.description or '',
                        'manager_name': manager_name,
                        'is_active': department.is_active,
                        'employee_count': department.employee_count,
                        'active_employee_count': department.active_employee_count,
                        'updated_at': department.updated_at.strftime('%b %d, %Y')
                    }
                })
            else:
                # Return form errors
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(e) for e in error_list]
                return JsonResponse({
                    'success': False,
                    'errors': errors
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': {'__all__': [str(e)]}
            }, status=500)
    
    return JsonResponse({'success': False, 'errors': {'__all__': ['Invalid request']}}, status=400)

@login_required
@require_http_methods(["POST"])
def delete_department(request, department_id):
    """Delete department via AJAX"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            department = get_object_or_404(Department, id=department_id)
            
            # Check if department has employees
            if department.employee_count > 0:
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot delete department "{department.name}" because it has {department.employee_count} employee(s). Please reassign or remove employees first.'
                }, status=400)
            
            department_name = department.name
            department.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Department "{department_name}" deleted successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting department: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)