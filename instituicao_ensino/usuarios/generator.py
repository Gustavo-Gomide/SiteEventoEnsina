"""
GERADOR DE CERTIFICADOS PROFISSIONAIS
=====================================
Gera certificados em PNG e PDF com design premium para eventos acadêmicos.
Utiliza tema vermelho vinho e dourado para transmitir elegância e nobreza.

Características:
- Template dinâmico com cores institucionais
- Tipografia hierárquica e elegante
- Elementos decorativos nobres
- QR code para verificação
- Saída em PNG e PDF de alta qualidade
"""

import os
import io
import uuid
from textwrap import wrap
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.text import slugify

def generate_certificates_for_event(evento_id):
    """
    GERA CERTIFICADOS PARA TODOS OS INSCRITOS VALIDADOS DE UM EVENTO
    =================================================================
    
    Parâmetros:
    - evento_id: ID do evento para o qual gerar os certificados
    
    Retorna:
    - Número de certificados gerados
    """
    
    # =========================================================================
    # IMPORTAÇÕES E CONFIGURAÇÕES INICIAIS
    # =========================================================================
    
    # Importações locais para evitar problemas de importação circular
    from eventos.models import Evento
    from usuarios.models import Certificado
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import qrcode

    # =========================================================================
    # CONFIGURAÇÕES DE CORES E DESIGN - TEMA VERMELHO VINHO E DOURADO
    # =========================================================================
    
    # Paleta de cores nobre para o certificado
    CORES = {
        'vinho_escuro': (139, 0, 0),      # #8B0000 - Vermelho vinho principal
        'vinho_medio': (120, 0, 0),       # #780000 - Vinho mais escuro
        'dourado_principal': (212, 175, 55),   # #D4AF37 - Dourado brilhante
        'dourado_escuro': (180, 150, 40), # #B49628 - Dourado para contornos
        'dourado_claro': (225, 190, 80),  # #E1BE50 - Dourado para realces
        'creme': (240, 235, 225),         # #FAF5EB - Fundo creme elegante
        'branco': (255, 255, 255),        # #FFFFFF - Branco puro
        'cinza_escuro': (20, 20, 20),     # #282828 - Texto principal
        'cinza_medio': (60, 60, 60),      # #505050 - Texto secundário
    }

    # =========================================================================
    # CONFIGURAÇÕES DE FONTES
    # =========================================================================
    
    # Busca o evento específico
    evento = Evento.objects.get(pk=evento_id)
    
    # Obtém todas as inscrições validadas
    inscricoes = evento.inscricaoevento_set.filter(is_validated=True)
    generated = 0

    def load_font(path, size):
        """
        CARREGA UMA FONTE DO SISTEMA OU USA FALLBACK
        """
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            return None

    # Lista de fontes preferidas (em ordem de prioridade)
    font_paths = [
        os.path.join(settings.BASE_DIR, "static", "fonts", "Montserrat-Bold.ttf"),
        os.path.join(settings.BASE_DIR, "static", "fonts", "Roboto-Bold.ttf"),
        "arialbd.ttf", 
        "DejaVuSans-Bold.ttf"
    ]

    font_paths_regular = [
        os.path.join(settings.BASE_DIR, "static", "fonts", "Montserrat-Regular.ttf"),
        os.path.join(settings.BASE_DIR, "static", "fonts", "Roboto-Regular.ttf"),
        "arial.ttf", 
        "DejaVuSans.ttf"
    ]

    font_paths_elegant = [
        os.path.join(settings.BASE_DIR, "static", "fonts", "PlayfairDisplay-Bold.ttf"),
        os.path.join(settings.BASE_DIR, "static", "fonts", "Georgia.ttf"),
        "timesbd.ttf"
    ]

    def pick_font(candidates, size):
        """
        SELECIONA A MELHOR FONTE DISPONÍVEL NA LISTA
        """
        for p in candidates:
            f = load_font(p, size)
            if f:
                return f
        return ImageFont.load_default()

    # Definição das fontes para cada elemento
    font_titulo_principal = pick_font(font_paths_elegant, 72)      # Título "CERTIFICADO"
    font_nome_participante = pick_font(font_paths_elegant, 58)     # Nome em destaque
    font_titulo_evento = pick_font(font_paths, 36)                 # Título do evento
    font_texto_corpo = pick_font(font_paths_regular, 28)           # Texto informativo
    font_texto_pequeno = pick_font(font_paths_regular, 20)         # Textos menores
    font_rodape = pick_font(font_paths_regular, 16)                # Rodapé e QR

    # =========================================================================
    # PROCESSAMENTO PARA CADA INSCRITO
    # =========================================================================
    
    for inscr in inscricoes:
        usuario = inscr.inscrito

        # =====================================================================
        # CONFIGURAÇÃO DE DIRETÓRIOS E ARQUIVOS
        # =====================================================================
        
        # Cria diretório específico para o usuário
        instituicao_nome = getattr(usuario.instituicao, "nome", "sem_instituicao")
        pasta_usuario = f"{usuario.nome_usuario}_{slugify(instituicao_nome)}"
        cert_dir = os.path.join(settings.MEDIA_ROOT, "usuarios", pasta_usuario, "certificados")
        os.makedirs(cert_dir, exist_ok=True)

        # Nome base do arquivo
        nome_base = f"{slugify(evento.titulo)}_{evento.data_fim.strftime('%Y_%m_%d') if evento.data_fim else 'sem_data'}"
        pdf_path = os.path.join(cert_dir, f"{nome_base}.pdf")
        png_path = os.path.join(cert_dir, f"{nome_base}.png")

        # Verifica se certificado já existe
        cert = Certificado.objects.filter(usuario=usuario, evento=evento).first()
        if cert and cert.pdf and getattr(cert.pdf, 'path', None) and os.path.exists(cert.pdf.path):
            continue  # Pula se já existir

        # Garante ID público único
        public_id = cert.public_id if cert and cert.public_id else str(uuid.uuid4())
        if not cert:
            cert = Certificado(usuario=usuario, evento=evento, public_id=public_id)
        else:
            if not cert.public_id:
                cert.public_id = public_id

        cert.nome = f"{evento.titulo} - {evento.data_fim.strftime('%Y-%m-%d') if evento.data_fim else ''}"

        # =====================================================================
        # CRIAÇÃO DO CERTIFICADO - DESIGN DINÂMICO
        # =====================================================================
        
        # Dimensões do certificado
        LARGURA, ALTURA = 1400, 990
        
        # Cria imagem base com fundo creme elegante
        certificado_img = Image.new("RGB", (LARGURA, ALTURA), CORES['creme'])
        draw = ImageDraw.Draw(certificado_img)

        # =====================================================================
        # ELEMENTOS DECORATIVOS DO CERTIFICADO
        # =====================================================================
        
        # 1. BORDAS ORNAMENTADAS
        # ======================
        
        # Borda externa dourada
        draw.rectangle([(0, 0), (LARGURA, ALTURA)], 
                      outline=CORES['dourado_principal'], width=20)
        
        # Borda interna vinho
        draw.rectangle([(30, 30), (LARGURA-30, ALTURA-30)], 
                      outline=CORES['vinho_escuro'], width=4)
        
        # Linha decorativa interna dourada
        draw.rectangle([(50, 50), (LARGURA-50, ALTURA-50)], 
                      outline=CORES['dourado_principal'], width=2)

        # 2. CABEÇALHO NOBRE
        # ===================
        
        altura_cabecalho = 120
        # Faixa superior vinho
        draw.rectangle([(0, 0), (LARGURA, altura_cabecalho)], 
                      fill=CORES['vinho_escuro'])
        
        # Linha decorativa abaixo do cabeçalho
        draw.line([(0, altura_cabecalho), (LARGURA, altura_cabecalho)], 
                 fill=CORES['dourado_principal'], width=6)

        # 3. ORNAMENTOS DECORATIVOS NOS CANTOS
        # ====================================
        
        def desenhar_ornamento_canto(x, y, tamanho=60):
            """Desenha elemento decorativo nos cantos do certificado"""
            # Pontos para criar forma ornamental
            pontos = [
                (x, y), (x + tamanho//3, y), (x + tamanho//2, y + tamanho//4),
                (x + tamanho*2//3, y), (x + tamanho, y), (x + tamanho, y + tamanho//3),
                (x + tamanho*3//4, y + tamanho//2), (x + tamanho, y + tamanho*2//3),
                (x + tamanho, y + tamanho), (x + tamanho*2//3, y + tamanho),
                (x + tamanho//2, y + tamanho*3//4), (x + tamanho//3, y + tamanho),
                (x, y + tamanho), (x, y + tamanho*2//3), (x + tamanho//4, y + tamanho//2),
                (x, y + tamanho//3)
            ]
            draw.polygon(pontos, fill=CORES['dourado_principal'])
        
        # Aplica ornamentos nos quatro cantos
        tamanho_ornamento = 60
        margem_ornamento = 40
        desenhar_ornamento_canto(margem_ornamento, margem_ornamento, tamanho_ornamento)
        desenhar_ornamento_canto(LARGURA - margem_ornamento - tamanho_ornamento, margem_ornamento, tamanho_ornamento)
        desenhar_ornamento_canto(margem_ornamento, ALTURA - margem_ornamento - tamanho_ornamento, tamanho_ornamento)
        desenhar_ornamento_canto(LARGURA - margem_ornamento - tamanho_ornamento, ALTURA - margem_ornamento - tamanho_ornamento, tamanho_ornamento)

        # 4. SELO DOURADO CENTRAL
        # =======================
        
        raio_selo = 50
        centro_x = LARGURA // 2
        centro_y = altura_cabecalho + 80
        
        # Círculo principal do selo
        draw.ellipse([(centro_x - raio_selo, centro_y - raio_selo),
                     (centro_x + raio_selo, centro_y + raio_selo)], 
                    fill=CORES['dourado_principal'], 
                    outline=CORES['dourado_escuro'], width=4)
        
        # Anel interno
        raio_interno = raio_selo - 12
        draw.ellipse([(centro_x - raio_interno, centro_y - raio_interno),
                     (centro_x + raio_interno, centro_y + raio_interno)], 
                    outline=CORES['dourado_escuro'], width=2)
        
        # Estrela central
        draw.regular_polygon((centro_x, centro_y, 20), 
                           n_sides=8, 
                           fill=CORES['vinho_escuro'], 
                           outline=CORES['dourado_escuro'])

        # =====================================================================
        # CONTEÚDO TEXTUAL DO CERTIFICADO
        # =====================================================================
        
        # 1. TÍTULO PRINCIPAL "CERTIFICADO"
        # =================================
        
        texto_titulo = "CERTIFICADO"
        pos_y_titulo = altura_cabecalho + 160
        
        # Sombra sutil para profundidade
        draw.text((LARGURA/2 + 3, pos_y_titulo + 3), texto_titulo, 
                 font=font_titulo_principal, 
                 fill=CORES['vinho_medio'], 
                 anchor="mm")
        
        # Texto principal
        draw.text((LARGURA/2, pos_y_titulo), texto_titulo, 
                 font=font_titulo_principal, 
                 fill=CORES['vinho_escuro'], 
                 anchor="mm")

        # 2. NOME DO PARTICIPANTE (DESTAQUE MÁXIMO)
        # ==========================================
        
        pos_y_nome = ALTURA * 0.45
        
        def desenhar_texto_com_contorno(pos, texto, fonte, cor_principal, cor_contorno, largura_contorno=3, anchor="mm"):
            """
            DESENHA TEXTO COM CONTORNO PARA DESTAQUE E LEGIBILIDADE
            """
            x, y = pos
            # Desenha contorno (multiples posições ao redor)
            for dx in range(-largura_contorno, largura_contorno + 1):
                for dy in range(-largura_contorno, largura_contorno + 1):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((x + dx, y + dy), texto, font=fonte, 
                             fill=cor_contorno, anchor=anchor)
            # Texto principal
            draw.text((x, y), texto, font=fonte, fill=cor_principal, anchor=anchor)
        
        # Aplica efeito especial ao nome
        desenhar_texto_com_contorno(
            pos=(LARGURA/2, pos_y_nome),
            texto=usuario.nome.upper(),
            fonte=font_nome_participante,
            cor_principal=CORES['dourado_principal'],
            cor_contorno=CORES['vinho_escuro'],
            largura_contorno=3
        )

        # 3. TEXTO DE OUTORGA
        # ===================
        
        texto_outorga = "é outorgado o presente certificado por ter participado do"
        pos_y_outorga = pos_y_nome + 80
        
        draw.text((LARGURA/2, pos_y_outorga), texto_outorga, 
                 font=font_texto_corpo, 
                 fill=CORES['cinza_escuro'], 
                 anchor="mm")

        # 4. TÍTULO DO EVENTO
        # ===================
        
        pos_y_evento = pos_y_outorga + 60
        
        # Quebra o título em múltiplas linhas se necessário
        titulo_linhas = wrap(evento.titulo, width=50)
        for i, linha in enumerate(titulo_linhas):
            draw.text((LARGURA/2, pos_y_evento + i * 40), linha, 
                     font=font_titulo_evento, 
                     fill=CORES['vinho_escuro'], 
                     anchor="mm")

        # 5. INFORMAÇÕES ADICIONAIS DO EVENTO
        # ====================================
        
        pos_y_info = pos_y_evento + len(titulo_linhas) * 45 + 40
        
        # Formata datas
        data_inicio = evento.data_inicio.strftime("%d/%m/%Y") if evento.data_inicio else "data não informada"
        data_fim = evento.data_fim.strftime("%d/%m/%Y") if evento.data_fim else None
        texto_data = data_inicio + (f" a {data_fim}" if data_fim else "")
        
        # Texto de horas
        texto_horas = f"({evento.horas} horas)" if getattr(evento, "horas", None) else ""
        
        # Linha de data e horas
        linha_data_horas = f"{texto_data} {texto_horas}".strip()
        draw.text((LARGURA/2, pos_y_info), linha_data_horas, 
                 font=font_texto_pequeno, 
                 fill=CORES['cinza_medio'], 
                 anchor="mm")

        # 6. INFORMAÇÕES DE ORGANIZAÇÃO
        # ==============================
        
        pos_y_org = pos_y_info + 40
        organizador = evento.organizador or "Organizador não informado"
        local_texto = evento.local or evento.modalidade or ""
        
        texto_organizacao = f"Organizado por: {organizador} • Local: {local_texto}"
        draw.text((LARGURA/2, pos_y_org), texto_organizacao, 
                 font=font_texto_pequeno, 
                 fill=CORES['cinza_medio'], 
                 anchor="mm")

        # =====================================================================
        # ELEMENTOS DE VALIDAÇÃO E RODAPÉ
        # =====================================================================
        
        # 1. QR CODE PARA VERIFICAÇÃO
        # ============================
        
        # Gera URL de verificação
        site = getattr(settings, "SITE_URL", "").rstrip("/")
        if site:
            cert_url = f"{site}/usuarios/certificado/{public_id}/"
        else:
            cert_url = f"/usuarios/certificado/{public_id}/"

        # Cria QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=8,
            border=1,
        )
        qr.add_data(cert_url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        tamanho_qr = 120
        qr_img = qr_img.resize((tamanho_qr, tamanho_qr), Image.LANCZOS)

        # Posiciona QR code no rodapé
        pos_x_qr = LARGURA - 120
        pos_y_qr = ALTURA - 140
        
        # Moldura dourada para o QR
        draw.rectangle([(pos_x_qr - 8, pos_y_qr - 8), 
                       (pos_x_qr + tamanho_qr + 8, pos_y_qr + tamanho_qr + 8)], 
                      outline=CORES['dourado_principal'], width=3)
        
        # Adiciona QR code à imagem principal
        certificado_img.paste(qr_img, (pos_x_qr, pos_y_qr))

        # Texto de verificação abaixo do QR
        draw.text((pos_x_qr + tamanho_qr/2, pos_y_qr + tamanho_qr + 25), 
                 "VERIFIQUE A AUTENTICIDADE", 
                 font=font_rodape, 
                 fill=CORES['vinho_escuro'], 
                 anchor="mm")

        # 2. LINHA DE RODAPÉ
        # ===================
        
        draw.line([(80, ALTURA - 60), (LARGURA - 80, ALTURA - 60)], 
                 fill=CORES['dourado_principal'], width=2)

        # 3. INFORMAÇÕES INSTITUCIONAIS NO RODAPÉ
        # ========================================
        
        instituicao_nome = getattr(evento.criador, "instituicao", "Instituição")
        draw.text((LARGURA/2, ALTURA - 80), 
                 f"{instituicao_nome} • EventoEnsina • www.eventoensina.com", 
                 font=font_rodape, 
                 fill=CORES['cinza_medio'], 
                 anchor="mm")

        # =====================================================================
        # MARCA D'ÁGUA DECORATIVA
        # =====================================================================
        
        try:
            # Cria marca d'água sutil com o título do evento
            marca_dagua = Image.new("RGBA", certificado_img.size, (250, 250, 250, 0))
            wdraw = ImageDraw.Draw(marca_dagua)
            
            # Usa fonte grande e transparente
            fonte_marca = pick_font(font_paths_elegant, 100)
            texto_marca = evento.titulo[:40]  # Limita tamanho
            
            wdraw.text((LARGURA * 0.5, ALTURA * 0.8), texto_marca, 
                      font=fonte_marca, 
                      fill=(139, 0, 0, 15),  # Vinho muito transparente
                      anchor="mm")
            
            # Aplica marca d'água
            certificado_img = Image.alpha_composite(
                certificado_img.convert("RGBA"), 
                marca_dagua
            ).convert("RGB")
        except Exception:
            pass  # Ignora erros na marca d'água

        # =====================================================================
        # SALVAMENTO DO CERTIFICADO PNG
        # =====================================================================
        
        # Prepara buffer para PNG
        png_buffer = io.BytesIO()
        certificado_img.save(png_buffer, format="PNG", optimize=True, quality=95)
        png_buffer.seek(0)

        # =====================================================================
        # GERAÇÃO DO PDF PROFISSIONAL
        # =====================================================================
        
        # Prepara buffer para PDF
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        
        # Configurações da página A4
        largura_a4, altura_a4 = A4
        
        # Converte a imagem para incluir no PDF
        img_reader = ImageReader(png_buffer)
        
        # Calcula dimensões mantendo proporção
        img_largura, img_altura = certificado_img.size
        escala = min(largura_a4 / img_largura, altura_a4 / img_altura) * 0.95
        nova_largura = img_largura * escala
        nova_altura = img_altura * escala
        
        # Centraliza na página
        x_pos = (largura_a4 - nova_largura) / 2
        y_pos = (altura_a4 - nova_altura) / 2
        
        # Insere imagem no PDF
        c.drawImage(img_reader, x_pos, y_pos, 
                   width=nova_largura, height=nova_altura, 
                   preserveAspectRatio=True, mask='auto')
        
        c.showPage()
        c.save()
        pdf_buffer.seek(0)

        # =====================================================================
        # SALVAMENTO NO BANCO DE DADOS
        # =====================================================================
        
        try:
            # Configura campo de upload se necessário
            setattr(cert, "_upload_field", "certificados")
        except Exception:
            pass

        # Salva arquivos PNG e PDF
        cert.png.save(f"{nome_base}.png", 
                     ContentFile(png_buffer.getvalue()), 
                     save=False)
        cert.pdf.save(f"{nome_base}.pdf", 
                     ContentFile(pdf_buffer.getvalue()), 
                     save=False)
        cert.save()

        generated += 1

    # =========================================================================
    # RETORNO FINAL
    # =========================================================================
    
    return generated