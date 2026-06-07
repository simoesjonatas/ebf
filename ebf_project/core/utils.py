import re
import qrcode
from io import BytesIO
import base64
from django.conf import settings
from django.core.exceptions import ValidationError


def validar_telefone(telefone):
    """Valida um telefone brasileiro. Aceita vazio (campo opcional). Quando
    preenchido, exige DDD + número: 10 dígitos (fixo) ou 11 (celular).
    Retorna o valor original (mantém a formatação digitada)."""
    telefone = (telefone or '').strip()
    if not telefone:
        return telefone
    digitos = re.sub(r'\D', '', telefone)
    if len(digitos) < 10 or len(digitos) > 11:
        raise ValidationError(
            'Telefone inválido. Informe DDD + número (10 ou 11 dígitos). Ex.: (11) 99999-9999.'
        )
    return telefone


def generate_qr_code(data, format='PNG'):
    """
    Gera um QR Code baseado nos dados fornecidos.
    Retorna a imagem em base64 para exibição em HTML.
    """
    qr = qrcode.QRCode(
        version=settings.QR_CODE_VERSION,
        error_correction=getattr(qrcode.constants, f'ERROR_CORRECT_{settings.QR_CODE_ERROR_CORRECTION}'),
        box_size=settings.QR_CODE_BOX_SIZE,
        border=settings.QR_CODE_BORDER,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format=format)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/{format.lower()};base64,{img_str}"


def get_qr_payload(tipo, token):
    """
    Gera o conteúdo seguro do QR Code sem URL navegável.
    Tipos: crianca, responsavel, checkout.
    """
    prefixos = {
        'crianca': 'EBF:CRI',
        'responsavel': 'EBF:RESP',
        'responsavel_checkin': 'EBF:RESP',
        'responsavel_checkout': 'EBF:RESP',
        'checkout': 'EBF:CHECKOUT',
        'checkin_lote': 'EBF:CHECKIN_LOTE',
        'checkout_lote': 'EBF:CHECKOUT_LOTE',
    }
    prefixo = prefixos.get(tipo, 'EBF:KEY')
    return f'{prefixo}:{token}'


def normalize_qr_payload(payload):
    """
    Lê QR Codes novos sem URL e mantém compatibilidade com QR antigo em URL.
    Retorna (tipo, token), onde tipo pode ser crianca, responsavel, checkout ou None.
    """
    valor = (payload or '').strip()
    if not valor:
        return None, ''

    if valor.startswith('EBF:CRI:'):
        return 'crianca', valor.replace('EBF:CRI:', '', 1)
    if valor.startswith('EBF:RESP:'):
        return 'responsavel', valor.replace('EBF:RESP:', '', 1)
    if valor.startswith('EBF:CHECKOUT:'):
        return 'checkout', valor.replace('EBF:CHECKOUT:', '', 1)
    if valor.startswith('EBF:CHECKIN_LOTE:'):
        return 'checkin_lote', valor.replace('EBF:CHECKIN_LOTE:', '', 1)
    if valor.startswith('EBF:CHECKOUT_LOTE:'):
        return 'checkout_lote', valor.replace('EBF:CHECKOUT_LOTE:', '', 1)

    # Compatibilidade com QR antigo que carregava URL inteira.
    if '/' in valor:
        token = valor.rstrip('/').split('/')[-1]
        if '/checkout/' in valor:
            return 'responsavel', token
        if '/checkin/crianca/' in valor:
            return 'crianca', token
        if '/checkin/responsavel/' in valor:
            return 'responsavel', token
        return None, token

    return None, valor


def get_qr_code_url(request, tipo, token):
    """Compatibilidade: agora retorna payload seguro, não URL."""
    return get_qr_payload(tipo, token)


def registrar_auditoria(usuario, acao, modelo, objeto_id, descricao='', ip_address=None):
    """
    Registra uma ação de auditoria.
    """
    from core.models import Auditoria
    Auditoria.objects.create(
        usuario=usuario,
        acao=acao,
        modelo=modelo,
        objeto_id=str(objeto_id),
        descricao=descricao,
        ip_address=ip_address
    )
