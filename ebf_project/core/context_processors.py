def user_profile(request):
    context = {
        'user_profile': None,
        'is_staff': False,
        'is_responsavel_user': False,
    }
    
    if request.user.is_authenticated:
        try:
            context['user_profile'] = request.user.perfil
            context['is_staff'] = request.user.perfil.is_staff_user()
        except Exception:
            pass
        try:
            context['is_responsavel_user'] = request.user.responsavel.ativo
        except Exception:
            pass
    
    return context
