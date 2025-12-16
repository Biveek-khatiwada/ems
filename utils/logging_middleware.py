import time
from django.utils.deprecation import MiddlewareMixin
from utils.logging_utils import Logger

class LoggingMiddleware(MiddlewareMixin):
    """Middleware to log all requests"""
    
    def process_request(self, request):
        """Store request start time"""
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log the request after it's processed"""
        try:
            # Calculate response time
            response_time = 0
            if hasattr(request, 'start_time'):
                response_time = time.time() - request.start_time
            
            # Get user info
            user = request.user if hasattr(request, 'user') else None
            username = user.username if user and user.is_authenticated else 'Anonymous'
            
            # Prepare log data
            log_data = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'response_time': round(response_time, 3),
                'content_length': len(response.content) if hasattr(response, 'content') else 0,
                'query_params': dict(request.GET),
            }
            
            # Determine log type based on status code
            if response.status_code >= 400:
                status = 'failed'
                log_type = 'error'
            else:
                status = 'success'
                log_type = 'view' if request.method == 'GET' else 'update'
            
            # Log the request
            Logger.log_activity(
                user=user if user and user.is_authenticated else None,
                log_type=log_type,
                module='system',
                action=f'{request.method} {request.path} - {response.status_code}',
                request=request,
                status=status,
                additional_data=log_data
            )
            
        except Exception as e:
            Logger.log_system_error('LoggingMiddleware', str(e))
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions"""
        import traceback
        Logger.log_system_error(
            source='Middleware',
            message=f'Exception in {request.method} {request.path}: {str(exception)}',
            traceback_text=traceback.format_exc(),
            additional_data={
                'method': request.method,
                'path': request.path,
                'user': request.user.username if request.user.is_authenticated else 'Anonymous'
            }
        )
        return None