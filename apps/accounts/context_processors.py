def acadify_user_context(request):
    """
    Provides global template variables for authenticated user profile,
    role, and quick notifications across all pages.
    """
    context = {
        'app_name': 'Acadify',
        'app_tagline': 'One Platform. Complete Academic Management.',
        'user_role': None,
        'user_profile': None,
    }

    if request.user.is_authenticated:
        user = request.user
        context['user_role'] = user.role
        if user.is_student_user:
            context['user_profile'] = getattr(user, 'student_profile', None)
        elif user.is_teacher_user:
            context['user_profile'] = getattr(user, 'teacher_profile', None)
        else:
            context['user_profile'] = None

    return context
