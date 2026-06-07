def user_profile(request):
    context = {
        'user_profile': None,
        'is_staff': False,
        'is_responsavel_user': False,
        'qr_code_responsavel': None,
    }

    if request.user.is_authenticated:
        try:
            context['user_profile'] = request.user.perfil
            context['is_staff'] = request.user.perfil.is_staff_user()
        except Exception:
            pass
        try:
            responsavel = request.user.responsavel
            if responsavel.ativo:
                context['is_responsavel_user'] = True
                # QR do responsável disponível em qualquer página (atalho na navbar)
                from core.utils import generate_qr_code, get_qr_payload
                context['qr_code_responsavel'] = generate_qr_code(
                    get_qr_payload('responsavel', responsavel.token_qr)
                )
                context['responsavel_nome'] = responsavel.nome_completo
        except Exception:
            pass

    return context
