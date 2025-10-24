"""
Usuarios models and storage helpers

This module contains models related to users and profile data. Key design
decisions:

- We keep a custom `Usuario` model for historical reasons. The project also
    stores a link to Django's `User` object in `Usuario.user` to gradually
    migrate to Django's auth system.
- Files uploaded for a user (profile photo, certificados) are stored under a
    stable `base_dir` inside `MEDIA_ROOT`. `Usuario.base_dir` is computed on
    first save and used afterwards so file paths don't change when display
    fields (nome_usuario/instituicao) are updated.
- The `user_directory_path` helper dynamically infers the subfolder for a
    specific FileField (e.g. 'foto_perfil', 'certificados'), sem depender de
    atributos transitórios (_upload_field).
"""

import re
import os
import shutil
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from .utils import create_user_dirs


# -----------------------------
# Tabela de DDD
# -----------------------------
class DDD(models.Model):
    codigo = models.CharField(max_length=5)  # Ex: "55"
    pais = models.CharField(max_length=50, default='Brasil')

    def __str__(self):
        return f"{self.codigo} ({self.pais})"


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
    telefone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nome


# -----------------------------
# Usuário
# -----------------------------
class Usuario(models.Model):
    nome = models.CharField(max_length=150)
    ddd = models.ForeignKey(DDD, on_delete=models.SET_NULL, null=True, blank=True)
    telefone = models.CharField(max_length=15, blank=True, null=True)
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
            ddd_num = self.ddd.codigo if self.ddd else ''
            # remove DDD do começo antes de validar
            if numero.startswith(ddd_num):
                numero_local = numero[len(ddd_num):]
            else:
                numero_local = numero

            if not re.match(r'^\d{8,9}$', numero_local):
                raise ValidationError("Telefone inválido. Exemplo aceito: 996135479")

    def save(self, *args, **kwargs):
        if self.senha and not self.senha.startswith('pbkdf2_'):
            self.senha = make_password(self.senha)

        if self.ddd and self.telefone:
            numero = re.sub(r'\D', '', self.telefone)
            ddd_num = self.ddd.codigo.lstrip('+')
            if not self.telefone.startswith('+'):
                self.telefone = f"+{ddd_num}{numero}"
            else:
                self.telefone = f"+{numero}"

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
        return check_password(senha, self.senha)

    def __str__(self):
        return f"{self.nome} ({self.tipo.tipo})"


# -----------------------------
# Caminho de upload
# -----------------------------
def user_directory_path(instance, filename):
    """Gera caminho para armazenar arquivos do usuário.

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
        super().save(*args, **kwargs)

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
