from django.db import models
import uuid
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone 
import datetime

class Department(models.Model):
    name = models.CharField(
        _("Department Name"),
        max_length=50,
        unique=True,
        blank=False,
        null=False
    )
    
    code = models.CharField(
        _("Department Code"),
        max_length=10,
        unique=True,
        blank=False,
        null=False
    )
    
    manager = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments'
    )
    
    description = models.TextField(
        _("Description"),
        blank=True,
        null=True
    )
    
    is_active = models.BooleanField(
        _("Is Active"),
        default=True
    )
    
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True
    )

    class Meta:
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"
    @property
    def employee_count(self):
        return self.employees.count() 
    
    @property
    def active_employee_count(self):
        return self.employees.filter(is_active=True).count()
    
    def get_active_employees(self):
        return self.employees.filter(is_active=True)
    
class CustomUser(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='custom_user_profile'
    )
    
    phone_number = models.BigIntegerField(
        _("Phone Number"),
        validators=[
            MinValueValidator(1000000000), 
            MaxValueValidator(999999999999999)  
        ],
        unique=True,
        blank=False,
        null=False,
        help_text=_("Enter 10-15 digit phone number")
    )
    
    # Changed from CharField to ForeignKey
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name=_("Department")
    )
    
    address = models.TextField(
        _("Address"),
        max_length=100,
        blank=False,
        null=False
    )
    
    # Add role field (optional but useful)
    ROLE_CHOICES = [
        ('employee', _('Employee')),
        ('manager', _('Manager')),
        ('admin', _('Administrator')),
    ]
    
    role = models.CharField(
        _("Role"),
        max_length=20,
        choices=ROLE_CHOICES,
        default='employee'
    )
    
    is_active = models.BooleanField(
        _("Is Active"),
        default=True
    )
    
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True
    )

    class Meta:
        verbose_name = _("Custom User")
        verbose_name_plural = _("Custom Users")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.department.name if self.department else 'No Department'}"
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def username(self):
        return self.user.username

    @classmethod
    def get_user_count(cls):
        return cls.objects.count()
    
    @classmethod
    def get_active_users(cls):
        return cls.objects.filter(is_active=True)
    
    @property
    def is_superadmin(self):
        """ check if user is a manager """
        return self.role =='admin' and self.user.is_superuser
    
    @property
    def is_department_manager(self):
        """ check if user is a manager """
        return self.role =='manager' and hasattr(self, 'department') and self.department is not None
    
    def can_edit_employee(self, employee):
        """ Check if the user can edit the given employee """
        if self.is_superadmin:
            return True
        if self.is_department_manager:
            return (
                employee.department == self.department and
                employee !='admin'
            )
        return self.id == employee.id
    
    

class Attendance(models.Model):
    ATTENDANCE_STATUS = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('leave', 'On Leave'),
        ('holiday', 'Holiday'),
        ('weekend', 'Weekend'),
    )
    
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='attendances')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='attendances', null=True, blank=True)
    date = models.DateField(default=timezone.now)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='absent')
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='marked_attendances')
    marked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date']
    
    def save(self, *args, **kwargs):

        if self.employee and self.employee.department:
            self.department = self.employee.department
        
        if self.check_in and self.check_out:
            check_in_dt = datetime.combine(self.date, self.check_in)
            check_out_dt = datetime.combine(self.date, self.check_out)
            diff = check_out_dt - check_in_dt
            self.total_hours = round(diff.total_seconds() / 3600, 2)
        
        super().save(*args, **kwargs)


class LeaveRequest(models.Model):
    LEAVE_TYPES = (
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('earned', 'Earned Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('unpaid', 'Unpaid Leave'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField(default=1)
    reason = models.TextField()
    supporting_docs = models.FileField(upload_to='leave_docs/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    response_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if self.start_date and self.end_date:
            self.total_days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)

    