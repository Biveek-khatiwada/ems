from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from emp.models import CustomUser, Department

@csrf_exempt
def toggle_employee_status(request, employee_id):
    if request.method == 'POST':
        try:
            employee = CustomUser.objects.get(id=employee_id)
            employee.is_active = not employee.is_active
            employee.save()
            return JsonResponse({
                'success': True,
                'is_active': employee.is_active,
                'message': f'Employee status updated to {"Active" if employee.is_active else "Inactive"}'
            })
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Employee not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def get_employee_details(request, employee_id):
    try:
        employee = CustomUser.objects.select_related('user', 'department').get(id=employee_id)
        data = {
            'id': str(employee.id),
            'full_name': employee.user.get_full_name() or employee.user.username,
            'username': employee.user.username,
            'email': employee.user.email,
            'phone_number': employee.phone_number,
            'address': employee.address,
            'department': employee.department.name if employee.department else 'No Department',
            'department_code': employee.department.code if employee.department else '',
            'role': employee.get_role_display(),
            'is_active': employee.is_active,
            'created_at': employee.created_at.strftime('%B %d, %Y'),
            'updated_at': employee.updated_at.strftime('%B %d, %Y %I:%M %p'),
        }
        return JsonResponse({'success': True, 'employee': data})
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee not found'})