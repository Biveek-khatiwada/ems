# In your app, create signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.utils import timezone
import json

from .models import ActivityLog, AuditLog, SystemLog, LoginLog

# Activity logging for model changes
@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    # Skip logging for certain models
    if sender.__name__ in ['ActivityLog', 'AuditLog', 'SystemLog', 'LoginLog']:
        return
    
    # Get request from instance if available
    request = getattr(instance, '_request', None)
    
    action = 'create' if created else 'update'
    
    ActivityLog.objects.create(
        user=request.user if request and hasattr(request, 'user') else None,
        log_type=action,
        module='system',  # You can customize this
        action=f'{action.capitalize()}d {sender.__name__}: {str(instance)}',
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT') if request else None,
        status='success'
    )

@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    # Skip logging for certain models
    if sender.__name__ in ['ActivityLog', 'AuditLog', 'SystemLog', 'LoginLog']:
        return
    
    # Get request from instance if available
    request = getattr(instance, '_request', None)
    
    ActivityLog.objects.create(
        user=request.user if request and hasattr(request, 'user') else None,
        log_type='delete',
        module='system',  # You can customize this
        action=f'Deleted {sender.__name__}: {str(instance)}',
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT') if request else None,
        status='success'
    )

# Login/logout logging
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        user=user,
        log_type='login',
        module='authentication',
        action=f'User {user.username} logged in',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        status='success'
    )
    
    LoginLog.objects.create(
        username=user.username,
        user=user,
        status='success',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        ActivityLog.objects.create(
            user=user,
            log_type='logout',
            module='authentication',
            action=f'User {user.username} logged out',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            status='success'
        )

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get('username', 'unknown')
    
    ActivityLog.objects.create(
        user=None,
        log_type='login',
        module='authentication',
        action=f'Failed login attempt for user: {username}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        status='failed'
    )
    
    LoginLog.objects.create(
        username=username,
        user=None,
        status='failed',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        failure_reason='Invalid credentials'
    )

# System error logging
import logging
from django.core.signals import got_request_exception

@receiver(got_request_exception)
def log_system_error(sender, request, **kwargs):
    import sys
    import traceback
    
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    SystemLog.objects.create(
        level='ERROR',
        source=sender.__class__.__name__ if hasattr(sender, '__class__') else str(sender),
        message=str(exc_value),
        traceback=tb_str,
        additional_data={
            'path': request.path if request else None,
            'method': request.method if request else None,
            'user': request.user.username if request and request.user.is_authenticated else None,
        }
    )