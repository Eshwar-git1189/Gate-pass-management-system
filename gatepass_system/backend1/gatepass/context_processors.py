def user_role(request):
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        user_type = request.user.profile.user_type
        return {
            'user_role': user_type,
            'is_warden': user_type == 'WARDEN',
            'is_security': user_type == 'SECURITY', 
            'is_student': user_type == 'STUDENT'
        }
    return {
        'user_role': None,
        'is_warden': False,
        'is_security': False,
        'is_student': False
    }
