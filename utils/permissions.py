from django.core.exceptions import PermissionDenied



class PermissionMixin:
    def admin_required(self,view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or not request.user.is_admin():
                raise PermissionDenied("You do not have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view

    def manager_required(self,view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or not request.user.is_manager():
                raise PermissionDenied("You do not have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view

    def staff_required(self,view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or not request.user.is_staff_user():
                raise PermissionDenied("You do not have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view

    def driver_required(self,view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or not request.user.is_driver():
                raise PermissionDenied("You do not have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
