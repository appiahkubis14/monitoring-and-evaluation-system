from functools import wraps
from django.http import HttpResponseForbidden

from django.core.exceptions import PermissionDenied
from functools import wraps

def group_required(*group_names):
    """
    Decorator to restrict access to users in specific groups.

    Args:
        group_names (tuple): Names of the groups allowed to access the view.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You do not have permission to access this page.")
        return _wrapped_view
    return decorator




def permission_required(perm, raise_exception=False):
    """
    Decorator to check if the user has a specific permission.

    Args:
        perm (str): The permission to check (e.g., "employees.view_employee").
        raise_exception (bool): Whether to raise a PermissionDenied exception.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.has_perm(perm):
                return view_func(request, *args, **kwargs)
            
            if raise_exception:
                raise PermissionDenied("You do not have permission to access this page.")
            return HttpResponseForbidden("You do not have permission to access this page.")
        
        return _wrapped_view
    return decorator
