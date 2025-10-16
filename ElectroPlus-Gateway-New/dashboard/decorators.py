from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def staff_required(function):
    """
    Decorator para verificar si el usuario es staff
    """
    def wrap(request, *args, **kwargs):
        if request.user.is_staff:
            return function(request, *args, **kwargs)
        raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap