from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render


def render_access_denied(request, mensagem='Seu perfil não possui permissão para acessar esta página.'):
    return render(request, 'core/access_denied.html', {'mensagem': mensagem}, status=403)


def usuario_tem_responsavel(user):
    if not user.is_authenticated:
        return False
    try:
        return user.responsavel.ativo
    except Exception:
        return False


def perfil_requerido(tipos_permitidos):
    """
    Libera a view quando o usuário é superuser ou staff do Django, OU possui um
    Perfil ativo cujo tipo está em tipos_permitidos (ex.: coordenacao, admin).
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or user.is_staff:
                return view_func(request, *args, **kwargs)
            try:
                perfil = user.perfil
            except ObjectDoesNotExist:
                perfil = None
            if perfil and perfil.ativo and perfil.tipo_perfil in tipos_permitidos:
                return view_func(request, *args, **kwargs)
            return render_access_denied(request, 'Você não tem permissão para acessar esta página.')
        return wrapper
    return decorator


def recepcao_requerida(view_func):
    return perfil_requerido(['recepcao', 'checkin', 'coordenacao', 'admin'])(view_func)


def checkout_requerido(view_func):
    return perfil_requerido(['recepcao', 'checkout', 'coordenacao', 'admin'])(view_func)


def coordenacao_requerida(view_func):
    return perfil_requerido(['coordenacao', 'admin'])(view_func)


def responsavel_requerido(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if usuario_tem_responsavel(request.user):
            return view_func(request, *args, **kwargs)
        return render_access_denied(request, 'Você precisa ter um cadastro de responsável para acessar esta página.')
    return wrapper


def professor_requerido(view_func):
    return perfil_requerido(['professor', 'coordenacao', 'admin'])(view_func)
