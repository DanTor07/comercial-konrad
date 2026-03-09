import logging
import json
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('audit')

class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to log CRUD operations on models.
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            # We focus on POST, PUT, DELETE for CRUD tracking
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                from ..services.monitoring import AuditService
                user = request.user
                path = request.path
                method = request.method
                
                message = f"ACTION: {method} | PATH: {path}"
                
                if request.POST:
                    post_data = request.POST.copy()
                    if 'password' in post_data:
                        post_data['password'] = '******'
                    message += f" | DATA: {json.dumps(post_data.dict())}"
                
                logger.info(f"USER: {user.username} | {message}")
                AuditService.log_action(user.id, method, message)
        
        return None
