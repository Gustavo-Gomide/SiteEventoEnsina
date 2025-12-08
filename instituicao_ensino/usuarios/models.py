"""
Modelos de usuários e utilitários de armazenamento

Este módulo contém os modelos relacionados a usuários e dados de perfil. Decisões de projeto:

- Mantemos um modelo customizado `Usuario` por razões históricas. O projeto também
    armazena um vínculo com o objeto `User` do Django em `Usuario.user` para migrar
    gradualmente para o sistema de autenticação do Django.
- Arquivos enviados por um usuário (foto de perfil, certificados) são armazenados em
    um `base_dir` estável dentro do `MEDIA_ROOT`. O campo `Usuario.base_dir` é calculado
    no primeiro save e usado depois, assim os caminhos dos arquivos não mudam quando
    campos de exibição (nome_usuario/instituicao) são atualizados.
- O helper `user_directory_path` infere dinamicamente a subpasta para um
    FileField específico (ex: 'foto_perfil', 'certificados'), sem depender de
    atributos transitórios (_upload_field).
"""

import re
import os
import shutil
import hashlib
import binascii
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django.conf import settings
from .utils import create_user_dirs, resize_image


# -----------------------------
# Nota sobre DDD
# -----------------------------
# A aplicação não armazena mais o DDD em campo separado. O campo `telefone`
# guarda o número completo em formato internacional: +CC (DD) NNNNN-NNNN.


# -----------------------------
# Tipos de Usuário
# -----------------------------
class TipoUsuario(models.Model):
    tipo = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.tipo


# -----------------------------
# Instituições de Ensino
# -----------------------------
class Instituicao(models.Model):
    nome = models.CharField(max_length=150)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=50, blank=True, null=True)
    pais = models.CharField(max_length=50, default='Brasil')
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=25, blank=True, null=True)

    def __str__(self):
        return self.nome


# -----------------------------
# Usuário
# -----------------------------
class Usuario(models.Model):
    nome = models.CharField(max_length=150)
    # armazenamos o telefone completo em formato internacional: +CC (AA) NNNNN-NNNN
    telefone = models.CharField(max_length=32, blank=True, null=True)
    instituicao = models.ForeignKey(Instituicao, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.ForeignKey(TipoUsuario, on_delete=models.CASCADE)
    nome_usuario = models.CharField(max_length=50, unique=True)
    email = models.EmailField(blank=True, null=True)
    senha = models.CharField(max_length=128, blank=True, null=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='profile')
    base_dir = models.CharField(max_length=255, blank=True, null=True)

    def clean(self):
        if self.tipo.tipo in ['Aluno', 'Professor'] and not self.instituicao:
            raise ValidationError("Alunos e Professores devem ter instituição cadastrada.")


        if self.telefone:
            numero = re.sub(r'\D', '', self.telefone)
            # Esperamos ao menos 11 dígitos (DDD 2 + número local 9). Pode haver
            # prefixo de país (1-3 dígitos) antes dos 11 dígitos.
            if len(numero) < 11:
                raise ValidationError("Telefone inválido. Informe pelo menos 11 dígitos: DDD + número local")
            if len(numero) > 13:
                raise ValidationError("Telefone inválido. Máximo esperado: código do país (até 3 dígitos) + DDD + número local")

    def save(self, *args, **kwargs):
        # Hash de senha: usamos PBKDF2 via hashlib para reforçar a criptografia.
        # Mantemos compatibilidade com hashes do Django (prefixo 'pbkdf2_').
        if self.senha and not (self.senha.startswith('pbkdf2_') or self.senha.startswith('pbkdf2_custom$')):
            # implementação PBKDF2-SHA256 (iterações elevadas)
            try:
                iterations = 200000
                salt = binascii.hexlify(os.urandom(16)).decode()
                dk = hashlib.pbkdf2_hmac('sha256', self.senha.encode(), salt.encode(), iterations)
                hashed = binascii.hexlify(dk).decode()
                # formato: pbkdf2_custom$sha256$<iterations>$<salt>$<hash>
                self.senha = f"pbkdf2_custom$sha256${iterations}${salt}${hashed}"
            except Exception:
                pass

        # Normaliza o telefone para o padrão internacional +CC (DD) NNNNN-NNNN
        if self.telefone:
            numero = re.sub(r'\D', '', self.telefone)
            # separa código do país (tudo antes dos últimos 11 dígitos)
            if len(numero) > 11:
                country = numero[:-11]
            else:
                country = '55'  # padrão Brasil quando país não informado

            core = numero[-11:]
            area = core[:2]
            local = core[2:]

            if len(local) == 9 and area:
                part1 = local[:5]
                part2 = local[5:]
                self.telefone = f"+{country} ({area}) {part1}-{part2}"

        nome_clean = str(self.nome_usuario).replace(' ', '_')
        instituicao = self.instituicao.nome if self.instituicao else 'sem_instituicao'
        instituicao_clean = str(instituicao).replace(' ', '_')
        desired_base = f'usuarios/{nome_clean}_{instituicao_clean}'

        old_base = None
        if self.pk:
            try:
                existing = Usuario.objects.get(pk=self.pk)
                old_base = existing.base_dir
            except Exception:
                old_base = None

        if old_base and old_base != desired_base:
            old_abs = os.path.join(settings.MEDIA_ROOT, old_base)
            new_abs = os.path.join(settings.MEDIA_ROOT, desired_base)
            try:
                os.makedirs(os.path.dirname(new_abs), exist_ok=True)
                if os.path.exists(old_abs):
                    shutil.move(old_abs, new_abs)
            except Exception:
                pass
            self.base_dir = desired_base
            super().save(*args, **kwargs)

            try:
                from .models import Perfil as PerfilModel, Certificado as CertModel
                perfil = getattr(self, 'perfil', None)
                if perfil and perfil.foto:
                    if perfil.foto.name and perfil.foto.name.startswith(old_base):
                        perfil.foto.name = perfil.foto.name.replace(old_base, desired_base, 1)
                        perfil.save()

                for cert in self.certificado_set.all():
                    changed = False
                    if cert.pdf and cert.pdf.name.startswith(old_base):
                        cert.pdf.name = cert.pdf.name.replace(old_base, desired_base, 1)
                        changed = True
                    if cert.png and cert.png.name.startswith(old_base):
                        cert.png.name = cert.png.name.replace(old_base, desired_base, 1)
                        changed = True
                    if cert.arquivo and cert.arquivo.name.startswith(old_base):
                        cert.arquivo.name = cert.arquivo.name.replace(old_base, desired_base, 1)
                        changed = True
                    if changed:
                        cert.save()
            except Exception:
                pass
            return

        if not self.base_dir:
            self.base_dir = desired_base

        super().save(*args, **kwargs)

    def check_senha(self, senha):
        # Suporta nosso formato customizado `pbkdf2_custom$sha256$<iter>$<salt>$<hash>`.
        if self.senha and self.senha.startswith('pbkdf2_custom$'):
            try:
                _prefix, alg, iterations, salt, stored_hash = self.senha.split('$')
                iterations = int(iterations)
                dk = hashlib.pbkdf2_hmac('sha256', senha.encode(), salt.encode(), iterations)
                return binascii.hexlify(dk).decode() == stored_hash
            except Exception:
                return False

        return check_password(senha, self.senha)

    def __str__(self):
        return f"{self.nome} ({self.tipo.tipo})"


# -----------------------------
# Caminho de upload
# -----------------------------
def user_directory_path(instance, filename):
    """Gera o caminho para armazenar arquivos do usuário.

    Formato:
        usuarios/<nome_usuario>_<instituicao>/<tipo_arquivo>/<filename>
    Exemplo:
        usuarios/aluno1_UniversidadeExemplo/foto_perfil/avatar.jpg
    """
    usuario = instance.usuario
    base = getattr(usuario, 'base_dir', None)
    if not base:
        nome = usuario.nome_usuario
        instituicao = usuario.instituicao.nome if usuario.instituicao else 'sem_instituicao'
        base = f"usuarios/{str(nome).replace(' ', '_')}_{str(instituicao).replace(' ', '_')}"

    # detecta o tipo de arquivo dinamicamente, sem depender de _upload_field
    if isinstance(instance, Perfil):
        subpasta = "foto_perfil"
        ext = os.path.splitext(filename)[1]  # mantém a extensão original
        filename = f"foto_perfil{ext}"
    elif isinstance(instance, Certificado):
        subpasta = "certificados"
    else:
        subpasta = "arquivos"

    return f"{base}/{subpasta}/{filename}"


# -----------------------------
# Perfil do Usuário
# -----------------------------
class Perfil(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    foto = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    biografia = models.TextField(blank=True, null=True)
    mostrar_email = models.BooleanField(default=False)
    mostrar_telefone = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        try:
            if getattr(self, 'usuario', None):
                create_user_dirs(self.usuario)
        except Exception:
            pass

        # Remove a foto antiga se for substituir
        try:
            if self.pk and self.foto:
                old_instance = Perfil.objects.filter(pk=self.pk).first()
                if old_instance and old_instance.foto and old_instance.foto != self.foto:
                    if old_instance.foto and os.path.exists(old_instance.foto.path):
                        os.remove(old_instance.foto.path)
        except Exception:
            pass

        super().save(*args, **kwargs)  # salva o objeto primeiro

        # Redimensiona a foto
        try:
            if self.foto and os.path.exists(self.foto.path):
                resize_image(self.foto.path, max_size=(400, 400), quality=70)
        except Exception:
            pass

    def __str__(self):
        return f'Perfil de {self.usuario.nome_usuario}'



# -----------------------------
# Certificados
# -----------------------------
class Certificado(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    evento = models.ForeignKey('eventos.Evento', on_delete=models.SET_NULL, null=True, blank=True)
    arquivo = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    pdf = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    png = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    qr_data = models.CharField(max_length=500, blank=True, null=True)
    nome = models.CharField(max_length=200, blank=True)
    horas = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    public_id = models.CharField(max_length=64, blank=True, null=True, unique=True)
    data_emitido = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        try:
            if getattr(self, 'usuario', None):
                create_user_dirs(self.usuario)
        except Exception:
            pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Certificado {self.nome or self.arquivo.name} de {self.usuario.nome_usuario}'


# -----------------------------
# Registro de Auditoria
# -----------------------------
class AuditLog(models.Model):
    """
    Armazena ações críticas para rastreabilidade.

    Campos:
    - timestamp: quando ocorreu
    - usuario: vínculo com o `usuarios.Usuario` quando aplicável
    - django_user: vínculo com o `auth.User` quando aplicável
    - action: string curta identificando a ação (ex: create_event)
    - object_type: tipo do objeto afetado (ex: Evento, InscricaoEvento)
    - object_id: id do objeto afetado (string para flexibilidade)
    - description: descrição legível
    - ip_address: IP do solicitante quando conhecido
    - extra: campo JSON para dados adicionais
    """
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True)
    django_user = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100, blank=True, null=True)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    extra = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        who = self.usuario.nome_usuario if self.usuario else (self.django_user.username if self.django_user else 'sistema')
        return f"[{self.timestamp}] {who} - {self.action} {self.object_type or ''} {self.object_id or ''}"
