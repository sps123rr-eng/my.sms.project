from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_admin_user or request.user.is_superuser):
            messages.error(request, "Access denied: Administrative privileges required.")
            return redirect('dashboard_redirect')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_teacher_user and not request.user.is_admin_user:
            messages.error(request, "Access denied: Faculty portal access only.")
            return redirect('dashboard_redirect')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def student_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_student_user and not request.user.is_admin_user:
            messages.error(request, "Access denied: Student portal access only.")
            return redirect('dashboard_redirect')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
