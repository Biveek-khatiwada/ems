from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import uuid

class ActivityLog(models.Model):
    """Model to track all user activities"""
    LOG_TYPES = [
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('create', _('Create')),
        ('update', _('Update')),
        ('delete', _('Delete')),
        ('view', _('View')),
        ('export', _('Export')),
        ('import', _('Import')),
        ('system', _('System Event')),
        ('error', _('Error')),
    ]
    
    MODULES = [
        ('employee', _('Employee')),
        ('department', _('Department')),
        ('user', _('User')),
        ('system', _('System')),
        ('authentication', _('Authentication')),
        ('report', _('Report')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    log_type = models.CharField(
        _("Log Type"),
        max_length=20,
        choices=LOG_TYPES
    )
    module = models.CharField(
        _("Module"),
        max_length=20,
        choices=MODULES
    )
    action = models.TextField(
        _("Action Description")
    )
    ip_address = models.GenericIPAddressField(
        _("IP Address"),
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        _("User Agent"),
        null=True,
        blank=True
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=[
            ('success', _('Success')),
            ('failed', _('Failed')),
            ('warning', _('Warning')),
        ],
        default='success'
    )
    additional_data = models.JSONField(
        _("Additional Data"),
        null=True,
        blank=True,
        default=dict
    )
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _("Activity Log")
        verbose_name_plural = _("Activity Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['log_type']),
            models.Index(fields=['module']),
        ]

    def __str__(self):
        return f"{self.get_log_type_display()} - {self.action[:50]}"


class AuditLog(models.Model):
    """Model to track all data changes for auditing purposes"""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(
        _("Action"),
        max_length=40,
        choices=[
            ('CREATE', _('Create')),
            ('UPDATE', _('Update')),
            ('DELETE', _('Delete')),
            ('SOFT_DELETE', _('Soft Delete')),
            ('RESTORE', _('Restore')),
        ]
    )
    model_name = models.CharField(
        _("Model Name"),
        max_length=100
    )
    object_id = models.CharField(
        _("Object ID"),
        max_length=100
    )
    object_repr = models.TextField(
        _("Object Representation")
    )
    changes = models.JSONField(
        _("Changes"),
        default=dict
    )
    ip_address = models.GenericIPAddressField(
        _("IP Address"),
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['model_name']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.object_id})"


class SystemLog(models.Model):
    """Model for system-level logs (errors, warnings, info)"""
    LOG_LEVELS = [
        ('DEBUG', _('Debug')),
        ('INFO', _('Info')),
        ('WARNING', _('Warning')),
        ('ERROR', _('Error')),
        ('CRITICAL', _('Critical')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    level = models.CharField(
        _("Log Level"),
        max_length=10,
        choices=LOG_LEVELS
    )
    source = models.CharField(
        _("Source"),
        max_length=100
    )
    message = models.TextField(
        _("Message")
    )
    traceback = models.TextField(
        _("Traceback"),
        null=True,
        blank=True
    )
    additional_data = models.JSONField(
        _("Additional Data"),
        null=True,
        blank=True,
        default=dict
    )
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _("System Log")
        verbose_name_plural = _("System Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['level']),
            models.Index(fields=['source']),
        ]

    def __str__(self):
        return f"[{self.level}] {self.source}: {self.message[:100]}"


class LoginLog(models.Model):
    """Specialized model for login attempts tracking"""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    username = models.CharField(
        _("Username"),
        max_length=150
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='login_logs'
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=[
            ('success', _('Success')),
            ('failed', _('Failed')),
            ('locked', _('Account Locked')),
            ('expired', _('Password Expired')),
        ]
    )
    ip_address = models.GenericIPAddressField(
        _("IP Address"),
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        _("User Agent"),
        null=True,
        blank=True
    )
    failure_reason = models.CharField(
        _("Failure Reason"),
        max_length=100,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _("Login Log")
        verbose_name_plural = _("Login Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['username']),
            models.Index(fields=['status']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f"{self.username} - {self.status} - {self.created_at}"