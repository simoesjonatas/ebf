import re
import qrcode
from io import BytesIO
import base64
from pathlib import Path
from PIL import Image, ImageOps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile


def comprimir_imagem(arquivo, lado_maximo=1000, qualidade=85):
    """Redimensiona e recomprime uma imagem enviada, devolvendo um arquivo
    pronto para salvar. Mantém a proporção (lado maior limitado a
    ``lado_maximo`` px), reencoda como JPEG com a ``qualidade`` informada e
    aplica a orientação do EXIF (corrige fotos "deitadas" tiradas no celular).

    Como a foto 3x4 é exibida pequena, isso derruba uma imagem de 6-8 MB para
    ~100-150 KB sem perda visível, economizando disco e banda. Se o arquivo
    não for uma imagem válida, devolve o original sem alterar."""
    try:
        imagem = Image.open(arquivo)
        # Aplica a rotação registrada no EXIF e descarta os metadados.
        imagem = ImageOps.exif_transpose(imagem)
    except Exception:
        # Não é uma imagem que o Pillow consiga abrir — deixa a validação de
        # content_type cuidar do erro; aqui só não processamos.
        arquivo.seek(0)
        return arquivo

    # JPEG não tem canal alfa: converte transparência/paleta para RGB.
    if imagem.mode in ('RGBA', 'P', 'LA'):
        fundo = Image.new('RGB', imagem.size, (255, 255, 255))
        imagem = imagem.convert('RGBA')
        fundo.paste(imagem, mask=imagem.split()[-1])
        imagem = fundo
    elif imagem.mode != 'RGB':
        imagem = imagem.convert('RGB')

    # Reduz mantendo a proporção (não amplia imagens menores).
    imagem.thumbnail((lado_maximo, lado_maximo), Image.LANCZOS)

    buffer = BytesIO()
    imagem.save(buffer, format='JPEG', quality=qualidade, optimize=True)
    buffer.seek(0)

    nome_base = Path(getattr(arquivo, 'name', 'foto')).stem or 'foto'
    nome = f'{nome_base}.jpg'
    return InMemoryUploadedFile(
        buffer, 'ImageField', nome, 'image/jpeg', buffer.getbuffer().nbytes, None
    )


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
