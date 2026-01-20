from django.shortcuts import render, redirect,get_object_or_404,HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, timedelta
import datetime
from emp.models import CustomUser, Department, Attendance, AttendanceSettings ,LeaveRequest
from emp.forms import CustomUserCreationForm
from django.http import JsonResponse
from django.contrib import messages
from emp.forms import DepartmentForm
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login, logout
import json

@login_required
def home_page(request):
    try:
        # Get the logged-in user's custom profile
        try:
            custom_user = request.user.custom_user_profile
        except CustomUser.DoesNotExist:
            return redirect('login')
        
        # Get filter parameters
        department_filter = request.GET.get('department', '')
        role_filter = request.GET.get('role', '')
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('q', '')
        page_number = request.GET.get('page', 1)
        
        # Start with base queryset based on user role
        if custom_user.role == 'admin' and request.user.is_superuser:
            # Super Admin can see all employees
            emp_details = CustomUser.objects.select_related('user', 'department').order_by('-created_at')
            
            # Get all departments for super admin
            departments = Department.objects.annotate(
                dept_employee_count=Count('employees')
            ).order_by('name')
            
        elif custom_user.role == 'manager':
            # Manager can only see employees from their department
            if custom_user.department:
                emp_details = CustomUser.objects.filter(
                    department=custom_user.department
                ).select_related('user', 'department').order_by('-created_at')
                
                # Get only manager's department and other active departments for filter
                departments = Department.objects.filter(
                    Q(id=custom_user.department.id) | Q(is_active=True)
                ).annotate(
                    dept_employee_count=Count('employees')
                ).order_by('name')
            else:
                # If manager has no department, they can only see themselves
                emp_details = CustomUser.objects.filter(id=custom_user.id).select_related('user', 'department')
                departments = Department.objects.none()
                
        else:
            # Regular employees can only see themselves
            emp_details = CustomUser.objects.filter(id=custom_user.id).select_related('user', 'department')
            departments = Department.objects.none()
        
        # Apply additional filters (only if user has permission to see filtered data)
        if department_filter and (custom_user.role == 'admin' or custom_user.role == 'manager'):
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
        
        # Calculate statistics based on user role
        if custom_user.role == 'admin' and request.user.is_superuser:
            # Super Admin gets full statistics
            total_employees = CustomUser.objects.count()
            active_employees = CustomUser.objects.filter(is_active=True).count()
            managers_count = CustomUser.objects.filter(role='manager').count()
            total_departments = Department.objects.filter(is_active=True).count()
            
            # Calculate new hires this month
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            new_hires_this_month = CustomUser.objects.filter(
                created_at__gte=current_month
            ).count()
            
        elif custom_user.role == 'manager' and custom_user.department:
            # Manager gets statistics for their department only
            dept_employees = CustomUser.objects.filter(department=custom_user.department)
            total_employees = dept_employees.count()
            active_employees = dept_employees.filter(is_active=True).count()
            managers_count = dept_employees.filter(role='manager').count()
            total_departments = 1  # Only their department
            
            # Calculate new hires this month in their department
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            new_hires_this_month = dept_employees.filter(
                created_at__gte=current_month
            ).count()
            
        else:
            # Regular employee gets minimal statistics
            total_employees = 1
            active_employees = 1 if custom_user.is_active else 0
            managers_count = 1 if custom_user.role == 'manager' else 0
            total_departments = 1 if custom_user.department else 0
            new_hires_this_month = 0
        
        # Calculate percentages
        active_percentage = round((active_employees / total_employees * 100) if total_employees > 0 else 0, 1)
        managers_percentage = round((managers_count / total_employees * 100) if total_employees > 0 else 0, 1)
        
        # Calculate average employees per department
        avg_employees_per_dept = round(total_employees / total_departments, 1) if total_departments > 0 else 0
        
        # Pagination
        paginator = Paginator(emp_details, 10)
        page_obj = paginator.get_page(page_number)
        
        # Get user's full name for display
        user_full_name = custom_user.full_name or request.user.username
        
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
            'user_role': custom_user.role,
            'user_full_name': user_full_name,
            'user_department': custom_user.department,
            'is_superadmin': custom_user.role == 'admin' and request.user.is_superuser,
            'is_manager': custom_user.role == 'manager',
            'is_employee': custom_user.role == 'employee',
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
            'user_role': 'employee',
            'user_full_name': 'User',
            'is_superadmin': False,
            'is_manager': False,
            'is_employee': True,
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

@csrf_exempt
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
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

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

# user login and logout functions 
@never_cache
def user_login(request):
    if request.user.is_authenticated:
        return redirect('emp:home_page')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            messages.success(request,f"welcome back, {user.get_full_name() or user.username }!")
            
            try:
                custom_user = user.custom_user_profile
                return redirect('emp:home_page')
            except:
                messages.info(request,'Please contact admin to set up your employee profile.')
                return redirect('emp:complete_profile')
        else:
            messages.error(request,"Invalid username or Password.")
    
    return render(request, 'emp/login.html')


@login_required
@never_cache
def user_logout(request):
    logout(request)
    messages.success(request,"you have been successfully logged out.")
    return redirect('emp:login')

@login_required
@never_cache
def complete_profile(request):
    if hasattr(request.user,'custom_user_profile'):
        return redirect('emp:home_page')
    
    if request.method =='POST':
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        CustomUser.objects.create(
            user = request.user,
            phone_number = phone_number,
            address = address,
            role = 'employee'
        )
        messages.success(request,'Profile completed successfully!')
        return redirect('emp:home_page')
    return render(request, 'emp/complete_profile.html')

@login_required
def my_profile(request):
    try:
        custom_user = request.user.custom_user_profile
    except CustomUser.DoesNotExist:
        messages.error(request, 'Profile not found. Please contact administrator.')
        return redirect('emp:home_page')
    
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        custom_user.phone_number = request.POST.get('phone_number', custom_user.phone_number)
        custom_user.address = request.POST.get('address', custom_user.address)
        custom_user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('emp:my_profile')
    
    return render(request, 'emp/my_profile.html', {
        'custom_user': custom_user,
        'user_role': custom_user.role,
        'user_department': custom_user.department,
        'is_superadmin': custom_user.role == 'admin' and request.user.is_superuser,
        'is_manager': custom_user.role == 'manager',
        'is_employee': custom_user.role == 'employee',
    })
    
# attendence

@login_required
def attendance_dashboard(request):
    """Attendance dashboard for managers"""
    if not request.user.custom_user_profile.is_manager:
        messages.error(request, "Only managers can access attendance dashboard")
        return redirect('emp:home_page')
    
    manager = request.user.custom_user_profile
    department = manager.department
    
    
    today = timezone.now().date()
    

    start_of_week = today - timedelta(days=today.weekday())
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    
    
    employees = CustomUser.objects.filter(department=department, is_active=True)
    

    today_attendance = Attendance.objects.filter(
        date=today,
        employee__department=department
    ).select_related('employee')
    
    week_attendance = Attendance.objects.filter(
        date__gte=start_of_week,
        date__lte=today,
        employee__department=department
    )
    
    
    present_today = today_attendance.filter(status='present').count()
    absent_today = employees.count() - present_today
    late_today = today_attendance.filter(
        check_in__gt=department.attendance_settings.late_threshold
    ).count()
    
    context = {
        'today': today,
        'employees': employees,
        'today_attendance': today_attendance,
        'week_dates': week_dates,
        'week_attendance': week_attendance,
        'present_today': present_today,
        'absent_today': absent_today,
        'late_today': late_today,
        'department': department,
        'attendance_settings': department.attendance_settings if hasattr(department, 'attendance_settings') else None,
    }
    
    return render(request, 'emp/attendance_dashboard.html', context)

@login_required
def mark_attendance(request):
    """Mark attendance for employees"""
    if not request.user.custom_user_profile.is_manager:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    if request.method == 'POST':
        data = json.loads(request.body)
        employee_id = data.get('employee_id')
        date_str = data.get('date')
        status = data.get('status')
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        notes = data.get('notes', '')
        
        try:
            employee = CustomUser.objects.get(id=employee_id)
            attendance_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            
            if employee.department != request.user.custom_user_profile.department:
                return JsonResponse({'success': False, 'error': 'Cannot mark attendance for employees in other departments'})
            
            attendance, created = Attendance.objects.update_or_create(
                employee=employee,
                date=attendance_date,
                defaults={
                    'status': status,
                    'check_in': check_in,
                    'check_out': check_out,
                    'notes': notes,
                    'marked_by': request.user
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Attendance marked successfully',
                'attendance_id': attendance.id,
                'created': created
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def bulk_mark_attendance(request):
    """Bulk mark attendance for multiple employees"""
    if not request.user.custom_user_profile.is_manager:
        messages.error(request, "Permission denied")
        return redirect('emp:attendance_dashboard')
    
    if request.method == 'POST':
        date_str = request.POST.get('date')
        status = request.POST.get('status')
        employee_ids = request.POST.getlist('employees')
        
        try:
            attendance_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            marked_count = 0
            
            for emp_id in employee_ids:
                employee = CustomUser.objects.get(id=emp_id)
                
                if employee.department != request.user.custom_user_profile.department:
                    continue
                
                Attendance.objects.update_or_create(
                    employee=employee,
                    date=attendance_date,
                    defaults={
                        'status': status,
                        'marked_by': request.user
                    }
                )
                marked_count += 1
            
            messages.success(request, f'Attendance marked for {marked_count} employees')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('emp:attendance_dashboard')

@login_required
def attendance_report(request, employee_id=None):
    """Generate attendance reports"""
    if not request.user.custom_user_profile.is_manager:
        messages.error(request, "Only managers can view reports")
        return redirect('emp:home_page')
    
    manager = request.user.custom_user_profile
    department = manager.department
    
    month = request.GET.get('month', timezone.now().month)
    year = request.GET.get('year', timezone.now().year)
    employee_filter = request.GET.get('employee', 'all')

    if employee_id:
        employee = get_object_or_404(CustomUser, id=employee_id, department=department)
        attendances = Attendance.objects.filter(
            employee=employee,
            date__year=year,
            date__month=month
        ).order_by('date')
        selected_employee = employee
    else:
        attendances = Attendance.objects.filter(
            employee__department=department,
            date__year=year,
            date__month=month
        ).select_related('employee').order_by('date')
        selected_employee = None
    
    
    summary = {
        'total_days': attendances.count(),
        'present': attendances.filter(status='present').count(),
        'absent': attendances.filter(status='absent').count(),
        'leave': attendances.filter(status='leave').count(),
        'half_day': attendances.filter(status='half_day').count(),
    }
    
    
    employees = CustomUser.objects.filter(department=department, is_active=True)
    
    context = {
        'attendances': attendances,
        'summary': summary,
        'month': month,
        'year': year,
        'employees': employees,
        'selected_employee': selected_employee,
        'employee_filter': employee_filter,
    }
    
    return render(request, 'emp/attendance_report.html', context)


@login_required
def manage_leave_requests(request):
    """Manage leave requests (approve/reject)"""
    if not request.user.custom_user_profile.is_manager:
        messages.error(request, "Only managers can manage leave requests")
        return redirect('emp:home_page')
    
    manager = request.user.custom_user_profile
    department = manager.department
    
    leave_requests = LeaveRequest.objects.filter(
        employee__department=department
    ).select_related('employee').order_by('-created_at')
    
    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        action = request.POST.get('action') 
        notes = request.POST.get('notes', '')
        
        try:
            leave_request = LeaveRequest.objects.get(id=leave_id)
            
            if action == 'approve':
                leave_request.status = 'approved'
                # Mark attendance as leave for the period
                current_date = leave_request.start_date
                while current_date <= leave_request.end_date:
                    Attendance.objects.update_or_create(
                        employee=leave_request.employee,
                        date=current_date,
                        defaults={
                            'status': 'leave',
                            'notes': f'Approved {leave_request.get_leave_type_display()}',
                            'marked_by': request.user
                        }
                    )
                    current_date += timedelta(days=1)
                
                messages.success(request, f"Leave request approved for {leave_request.employee.user.get_full_name()}")
            else:
                leave_request.status = 'rejected'
                messages.success(request, f"Leave request rejected for {leave_request.employee.user.get_full_name()}")
            
            leave_request.reviewed_by = request.user
            leave_request.reviewed_at = timezone.now()
            leave_request.response_notes = notes
            leave_request.save()
            
        except LeaveRequest.DoesNotExist:
            messages.error(request, "Leave request not found")
    
    context = {
        'leave_requests': leave_requests,
        'department': department,
    }
    
    return render(request, 'emp/manage_leaves.html', context)


from emp.models import CustomUser, Department, Attendance, AttendanceSettings ,LeaveRequest

@login_required
def attendance_settings(request):
    """Configure attendance settings for department"""
    if not request.user.custom_user_profile.is_manager:
        messages.error(request, "Only managers can configure settings")
        return redirect('emp:home_page')
    
    manager = request.user.custom_user_profile
    department = manager.department
    
    # Get or create settings
    settings, created =  AttendanceSettings.objects.get_or_create(
        department=department,
        defaults={'created_by': request.user}
    )
    
    if request.method == 'POST':
        settings.working_hours = request.POST.get('working_hours')
        settings.late_threshold = request.POST.get('late_threshold')
        settings.half_day_threshold = request.POST.get('half_day_threshold')
        settings.check_in_start = request.POST.get('check_in_start')
        settings.check_in_end = request.POST.get('check_in_end')
        settings.check_out_start = request.POST.get('check_out_start')
        settings.check_out_end = request.POST.get('check_out_end')
        settings.weekdays = ','.join(request.POST.getlist('weekdays'))
        
        # Handle holidays
        holidays = request.POST.get('holidays', '')
        if holidays:
            settings.holidays = [h.strip() for h in holidays.split(',')]
        
        settings.save()
        messages.success(request, "Attendance settings updated successfully")
        return redirect('emp:attendance_settings')
    
    context = {
        'settings': settings,
        'department': department,
        'weekday_choices': [
            (1, 'Monday'),
            (2, 'Tuesday'),
            (3, 'Wednesday'),
            (4, 'Thursday'),
            (5, 'Friday'),
            (6, 'Saturday'),
            (7, 'Sunday'),
        ]
    }
    
    return render(request, 'emp/attendance_settings.html', context)

#Apis

@login_required
def get_employee_attendance(request, employee_id):
    """API endpoint to get employee attendance data"""
    if not request.user.custom_user_profile.is_manager:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        employee = CustomUser.objects.get(id=employee_id)
        
        if employee.department != request.user.custom_user_profile.department:
            return JsonResponse({'success': False, 'error': 'Cannot access employee from other department'})
        
        date_str = request.GET.get('date', timezone.now().date().isoformat())
        date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        
        attendance = Attendance.objects.filter(
            employee=employee,
            date=date
        ).first()
        
        if attendance:
            data = {
                'success': True,
                'attendance': {
                    'id': attendance.id,
                    'status': attendance.status,
                    'status_display': attendance.get_status_display(),
                    'check_in': attendance.check_in.isoformat() if attendance.check_in else None,
                    'check_out': attendance.check_out.isoformat() if attendance.check_out else None,
                    'total_hours': float(attendance.total_hours) if attendance.total_hours else 0,
                    'notes': attendance.notes,
                }
            }
        else:
            data = {
                'success': True,
                'attendance': None
            }
        
        return JsonResponse(data)
        
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def monthly_attendance_summary(request):
    """API endpoint to get monthly attendance summary"""
    if not request.user.custom_user_profile.is_manager:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        manager = request.user.custom_user_profile
        department = manager.department
        
        month = request.GET.get('month', timezone.now().month)
        year = request.GET.get('year', timezone.now().year)
        
        # Get attendance for the month
        attendances = Attendance.objects.filter(
            employee__department=department,
            date__year=year,
            date__month=month
        )
        
        # Calculate summary
        employees = CustomUser.objects.filter(department=department, is_active=True)
        total_days = attendances.count()
        
        summary = {
            'total_employees': employees.count(),
            'total_days': total_days,
            'present': attendances.filter(status='present').count(),
            'absent': attendances.filter(status='absent').count(),
            'late': attendances.filter(status='late').count(),
            'leave': attendances.filter(status='leave').count(),
            'half_day': attendances.filter(status='half_day').count(),
        }
        
        return JsonResponse({
            'success': True,
            'summary': summary,
            'month': month,
            'year': year
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_daily_attendance(request):
    """Get attendance for a specific date"""
    if not request.user.custom_user_profile.is_manager:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        date_str = request.GET.get('date', timezone.now().date().isoformat())
        date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        
        manager = request.user.custom_user_profile
        department = manager.department
        
        
        employees = CustomUser.objects.filter(department=department, is_active=True)
        
        # Get attendance for the date
        attendance_data = Attendance.objects.filter(
            employee__department=department,
            date=date
        ).select_related('employee')
        
        
        attendance_dict = {att.employee_id: att for att in attendance_data}
        
        # Prepare response data
        data = []
        for employee in employees:
            attendance = attendance_dict.get(employee.id)
            data.append({
                'employee_id': employee.id,
                'employee_name': employee.user.get_full_name() or employee.user.username,
                'username': employee.user.username,
                'status': attendance.status if attendance else 'absent',
                'status_display': attendance.get_status_display() if attendance else 'Absent',
                'check_in': attendance.check_in.isoformat() if attendance and attendance.check_in else None,
                'check_out': attendance.check_out.isoformat() if attendance and attendance.check_out else None,
                'total_hours': float(attendance.total_hours) if attendance and attendance.total_hours else 0,
                'notes': attendance.notes if attendance else '',
            })
        
        return JsonResponse({
            'success': True,
            'date': date_str,
            'data': data,
            'total_employees': employees.count(),
            'present_count': len([d for d in data if d['status'] == 'present']),
            'absent_count': len([d for d in data if d['status'] == 'absent']),
            'late_count': len([d for d in data if d['status'] == 'late']),
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})