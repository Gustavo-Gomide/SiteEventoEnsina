from django import forms
from .models import Usuario, DDD
from .models import Perfil, Certificado
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CadastroUsuarioForm(forms.ModelForm):
    senha = forms.CharField(widget=forms.PasswordInput)
    
    # Spinner de DDD
    ddd = forms.ModelChoiceField(
        queryset=DDD.objects.all(),
        empty_label="DDD"
    )

    # Telefone com placeholder
    telefone = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'EX: 98567-8901'})
    )

    class Meta:
        model = Usuario
        fields = ['nome', 'tipo', 'instituicao', 'nome_usuario', 'email', 'senha', 'ddd', 'telefone']

    def save(self, commit=True):
        # Cria User do Django e associa ao Usuario
        usuario = super().save(commit=False)
        senha = self.cleaned_data.get('senha')
        username = self.cleaned_data.get('nome_usuario')
        if not usuario.user:
            user = User.objects.create_user(username=username, password=senha)
            usuario.user = user
        else:
            # atualizar senha se informado
            if senha:
                usuario.user.set_password(senha)
                usuario.user.save()
        # salvar senha legacy hash (opcional)
        usuario.senha = usuario.user.password
        if commit:
            usuario.save()
            # garantir criação das pastas de mídia para o novo usuário
            try:
                from .utils import create_user_dirs
                create_user_dirs(usuario)
            except Exception:
                # não falhar a criação do usuário se a pasta não puder ser criada
                pass
        return usuario


class LoginForm(forms.Form):
    nome_usuario = forms.CharField(label="Usuário")
    senha = forms.CharField(widget=forms.PasswordInput)


class PerfilForm(forms.ModelForm):
    foto = forms.ImageField(required=False)

    mostrar_email = forms.BooleanField(required=False, label='Mostrar e-mail no perfil público')
    mostrar_telefone = forms.BooleanField(required=False, label='Mostrar telefone no perfil público')

    class Meta:
        model = Perfil
        fields = ['foto', 'biografia', 'mostrar_email', 'mostrar_telefone']

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        if not foto:
            return foto
        # limitar tamanho a 5MB
        if foto.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Tamanho máximo da foto: 5MB')
        # validar tipo
        main, sub = foto.content_type.split('/')
        if main != 'image' or sub not in ['jpeg', 'png']:
            raise forms.ValidationError('Formato inválido. Envie JPEG ou PNG.')
        return foto


class UsuarioEditForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nome', 'nome_usuario', 'email', 'instituicao']

    def clean_nome_usuario(self):
        nome_usuario = self.cleaned_data['nome_usuario']
        qs = Usuario.objects.filter(nome_usuario=nome_usuario)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Este nome de usuário já está em uso.')
        return nome_usuario


class CertificadoUploadForm(forms.ModelForm):
    class Meta:
        model = Certificado
        fields = ['arquivo', 'nome']

    def clean_arquivo(self):
        arquivo = self.cleaned_data.get('arquivo')
        if not arquivo:
            return arquivo
        # limitar a 20MB
        if arquivo.size > 20 * 1024 * 1024:
            raise forms.ValidationError('Tamanho máximo do certificado: 20MB')
        # permitir pdfs e imagens
        content_type = arquivo.content_type
        allowed = ['application/pdf', 'image/jpeg', 'image/png']
        if content_type not in allowed:
            raise forms.ValidationError('Formato inválido. Aceitamos PDF, JPEG ou PNG.')
        return arquivo
