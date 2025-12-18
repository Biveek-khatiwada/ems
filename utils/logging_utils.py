import json
import traceback
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
from .models import ActivityLog, AuditLog, SystemLog, LoginLog

class Logger:
    """Central logging utility class"""
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def get_user_agent(request):
        """Get user agent from request"""
        return request.META.get('HTTP_USER_AGENT', '')
    
    @classmethod
    def log_activity(cls, user, log_type, module, action, request=None, 
                     status='success', additional_data=None):
        """Log user activity"""
        try:
            ip_address = cls.get_client_ip(request) if request else None
            user_agent = cls.get_user_agent(request) if request else None
            
            ActivityLog.objects.create(
                user=user,
                log_type=log_type,
                module=module,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                additional_data=additional_data or {}
            )
        except Exception as e:
            cls.log_system_error('Logger.log_activity', str(e))
    
    @classmethod
    def log_audit(cls, user, action, model_name, object_id, 
                  object_repr, changes, request=None):
        """Log data changes for auditing"""
        try:
            ip_address = cls.get_client_ip(request) if request else None
            
            AuditLog.objects.create(
                user=user,
                action=action,
                model_name=model_name,
                object_id=str(object_id),
                object_repr=object_repr,
                changes=changes,
                ip_address=ip_address
            )
        except Exception as e:
            cls.log_system_error('Logger.log_audit', str(e))
    
    @classmethod
    def log_system(cls, level, source, message, traceback_text=None, additional_data=None):
        """Log system events"""
        try:
            SystemLog.objects.create(
                level=level,
                source=source,
                message=message,
                traceback=traceback_text,
                additional_data=additional_data or {}
            )
        except Exception as e:
            print(f"Failed to log system event: {e}")
    
    @classmethod
    def log_system_info(cls, source, message, additional_data=None):
        """Log system info"""
        cls.log_system('INFO', source, message, additional_data=additional_data)
    
    @classmethod
    def log_system_warning(cls, source, message, additional_data=None):
        """Log system warning"""
        cls.log_system('WARNING', source, message, additional_data=additional_data)
    
    @classmethod
    def log_system_error(cls, source, message, traceback_text=None, additional_data=None):
        """Log system error"""
        cls.log_system('ERROR', source, message, traceback_text, additional_data)
    
    @classmethod
    def log_login_attempt(cls, username, status, request=None, 
                         failure_reason=None, user=None):
        """Log login attempts"""
        try:
            ip_address = cls.get_client_ip(request) if request else None
            user_agent = cls.get_user_agent(request) if request else None
            
            LoginLog.objects.create(
                username=username,
                user=user,
                status=status,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=failure_reason
            )
            
            # Log activity as well
            if status == 'success' and user:
                cls.log_activity(
                    user=user,
                    log_type='login',
                    module='authentication',
                    action=f'User {username} logged in successfully',
                    request=request,
                    status='success'
                )
            else:
                cls.log_activity(
                    user=None,
                    log_type='system',
                    module='authentication',
                    action=f'Failed login attempt for username: {username}',
                    request=request,
                    status='failed',
                    additional_data={'failure_reason': failure_reason}
                )
        except Exception as e:
            cls.log_system_error('Logger.log_login_attempt', str(e))


# Django signals for automatic auditing
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User

class ModelAuditor:
    """Automatic model change tracking"""
    
    @staticmethod
    def get_changes(instance, created=False):
        """Get changes between old and new instance"""
        if not instance.pk or created:
            return {}
        
        try:
            old_instance = instance.__class__.objects.get(pk=instance.pk)
            changes = {}
            
            for field in instance._meta.fields:
                field_name = field.name
                old_value = getattr(old_instance, field_name, None)
                new_value = getattr(instance, field_name, None)
                
                # Handle special cases
                if field_name in ['password', 'created_at', 'updated_at']:
                    continue
                
                if old_value != new_value:
                    changes[field_name] = {
                        'old': str(old_value) if old_value is not None else None,
                        'new': str(new_value) if new_value is not None else None
                    }
            
            return changes
        except instance.__class__.DoesNotExist:
            return {}
    
    @classmethod
    def track_model(cls, model_class, request=None, user=None):
        """Decorator to track model changes"""
        @receiver(pre_save, sender=model_class)
        def pre_save_handler(sender, instance, **kwargs):
            """Store instance state before save"""
            if not instance.pk:
                instance._old_state = {}
            else:
                try:
                    old_instance = sender.objects.get(pk=instance.pk)
                    instance._old_state = {
                        field.name: getattr(old_instance, field.name, None)
                        for field in instance._meta.fields
                    }
                except sender.DoesNotExist:
                    instance._old_state = {}
        
        @receiver(post_save, sender=model_class)
        def post_save_handler(sender, instance, created, **kwargs):
            """Log save operations"""
            action = 'CREATE' if created else 'UPDATE'
            
            # Get changes
            changes = {}
            if hasattr(instance, '_old_state') and not created:
                for field in instance._meta.fields:
                    field_name = field.name
                    if field_name in ['password', 'created_at', 'updated_at']:
                        continue
                    
                    old_value = instance._old_state.get(field_name)
                    new_value = getattr(instance, field_name, None)
                    
                    if old_value != new_value:
                        changes[field_name] = {
                            'old': str(old_value) if old_value is not None else None,
                            'new': str(new_value) if new_value is not None else None
                        }
            
            # Clean up
            if hasattr(instance, '_old_state'):
                del instance._old_state
            
            # Log the audit
            Logger.log_audit(
                user=user or (request.user if request and hasattr(request, 'user') else None),
                action=action,
                model_name=sender.__name__,
                object_id=instance.pk,
                object_repr=str(instance),
                changes=changes,
                request=request
            )
            
            # Log activity
            if action == 'CREATE':
                activity_msg = f'Created {sender.__name__.lower()}: {instance}'
                log_type = 'create'
            else:
                activity_msg = f'Updated {sender.__name__.lower()}: {instance}'
                log_type = 'update'
            
            Logger.log_activity(
                user=user or (request.user if request and hasattr(request, 'user') else None),
                log_type=log_type,
                module=sender.__name__.lower(),
                action=activity_msg,
                request=request,
                status='success'
            )
        
        @receiver(post_delete, sender=model_class)
        def post_delete_handler(sender, instance, **kwargs):
            """Log delete operations"""
            Logger.log_audit(
                user=user or (request.user if request and hasattr(request, 'user') else None),
                action='DELETE',
                model_name=sender.__name__,
                object_id=instance.pk,
                object_repr=str(instance),
                changes={},
                request=request
            )
            
            Logger.log_activity(
                user=user or (request.user if request and hasattr(request, 'user') else None),
                log_type='delete',
                module=sender.__name__.lower(),
                action=f'Deleted {sender.__name__.lower()}: {instance}',
                request=request,
                status='success'
            )
        
        return pre_save_handler, post_save_handler, post_delete_handler