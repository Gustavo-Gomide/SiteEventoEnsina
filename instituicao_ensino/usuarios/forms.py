from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Usuario, DDD, Perfil, Certificado
import re


# ============================================================
# FORMULÁRIO DE CADASTRO DE USUÁRIO
# ============================================================
class CadastroUsuarioForm(forms.ModelForm):
    """
    Formulário para criar um novo usuário:
    - Salva no modelo custom `Usuario` e no `User` do Django.
    - Permite DDD separado do telefone.
    - Sincroniza senha criptografada com o User.
    """
    senha = forms.CharField(widget=forms.PasswordInput)

    # Spinner para selecionar DDD
    ddd = forms.ModelChoiceField(
        queryset=DDD.objects.all(),
        empty_label="DDD",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Campo telefone, mostra apenas o número local
    telefone = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'EX: 996135479', 'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = ['nome', 'tipo', 'instituicao', 'nome_usuario', 'email', 'senha', 'ddd', 'telefone']

    def save(self, commit=True):
        """
        Salva o usuário e o objeto User do Django, garantindo criação de pastas de mídia.
        """
        usuario = super().save(commit=False)
        senha = self.cleaned_data.get('senha')
        username = self.cleaned_data.get('nome_usuario')

        # Cria User do Django se não existir
        if not usuario.user:
            user = User.objects.create_user(username=username, password=senha)
            usuario.user = user
        else:
            # Atualiza senha caso informada
            if senha:
                usuario.user.set_password(senha)
                usuario.user.save()

        # Sincroniza a senha criptografada no campo legacy
        usuario.senha = usuario.user.password

        # Salva o usuário e cria diretórios de mídia
        if commit:
            usuario.save()
            try:
                from .utils import create_user_dirs
                create_user_dirs(usuario)
            except Exception:
                pass  # não falha se não conseguir criar diretórios

        return usuario


# ============================================================
# FORMULÁRIO DE LOGIN
# ============================================================
class LoginForm(forms.Form):
    """
    Formulário simples de login por usuário e senha.
    """
    nome_usuario = forms.CharField(label="Usuário")
    senha = forms.CharField(widget=forms.PasswordInput)


# ============================================================
# FORMULÁRIO DE PERFIL
# ============================================================
class PerfilForm(forms.ModelForm):
    """
    Permite editar:
    - Foto de perfil
    - Biografia
    - Visibilidade de email e telefone
    """
    foto = forms.ImageField(required=False)
    mostrar_email = forms.BooleanField(required=False, label='Mostrar e-mail no perfil público')
    mostrar_telefone = forms.BooleanField(required=False, label='Mostrar telefone no perfil público')

    class Meta:
        model = Perfil
        fields = ['foto', 'biografia', 'mostrar_email', 'mostrar_telefone']

    def clean_foto(self):
        """
        Valida foto de perfil:
        - Limite 5MB
        - Formato JPEG ou PNG
        - Só valida se o arquivo for novo enviado pelo form (tem content_type)
        """
        foto = self.cleaned_data.get('foto')
        if not foto:
            return foto

        if hasattr(foto, 'content_type'):
            if foto.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Tamanho máximo da foto: 5MB')
            main, sub = foto.content_type.split('/')
            if main != 'image' or sub not in ['jpeg', 'png']:
                raise forms.ValidationError('Formato inválido. Envie JPEG ou PNG.')
        return foto


# ============================================================
# FORMULÁRIO DE EDIÇÃO DE USUÁRIO
# ============================================================
class UsuarioEditForm(forms.ModelForm):
    ddd = forms.ModelChoiceField(
        queryset=DDD.objects.all(),
        required=False,
        empty_label="DDD",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    telefone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: 996524046', 'class': 'form-control'})
    )
    nova_senha = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Digite nova senha', 'class': 'form-control', 'id': 'id_senha'}),
        label="Nova senha"
    )

    class Meta:
        model = Usuario
        # remove 'senha' daqui, só campos de dados normais
        fields = ['nome', 'nome_usuario', 'email', 'instituicao', 'ddd', 'telefone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.telefone:
            tel = self.instance.telefone
            if tel.startswith('+') and self.instance.ddd:
                ddd_str = self.instance.ddd.codigo
                self.initial['telefone'] = tel.replace(ddd_str, '', 1)
            else:
                self.initial['telefone'] = tel

    def clean_nome_usuario(self):
        nome_usuario = self.cleaned_data['nome_usuario']
        qs = Usuario.objects.filter(nome_usuario=nome_usuario)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Este nome de usuário já está em uso.')
        return nome_usuario

    def save(self, commit=True):
        usuario = super().save(commit=False)
        nova_senha = self.cleaned_data.get('nova_senha')
        if nova_senha and usuario.user:
            usuario.user.set_password(nova_senha)
            usuario.user.save()
            usuario.senha = usuario.user.password
        if commit:
            usuario.save()
        return usuario

# ============================================================
# FORMULÁRIO DE UPLOAD DE CERTIFICADO
# ============================================================
class CertificadoUploadForm(forms.ModelForm):
    """
    Formulário para upload de certificados:
    - Permite PDF ou imagens (JPEG/PNG)
    - Limite 20MB
    """
    class Meta:
        model = Certificado
        fields = ['arquivo', 'nome']

    def clean_arquivo(self):
        arquivo = self.cleaned_data.get('arquivo')
        if not arquivo:
            return arquivo

        if arquivo.size > 20 * 1024 * 1024:
            raise forms.ValidationError('Tamanho máximo do certificado: 20MB')

        content_type = getattr(arquivo, 'content_type', None)
        allowed = ['application/pdf', 'image/jpeg', 'image/png']
        if content_type and content_type not in allowed:
            raise forms.ValidationError('Formato inválido. Aceitamos PDF, JPEG ou PNG.')
        return arquivo
