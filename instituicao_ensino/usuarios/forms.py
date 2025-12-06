from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Usuario, Perfil, Certificado, Instituicao
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
    senha_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirme a senha')
    # Tornar email e telefone obrigatórios
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Ex: voce@exemplo.com',
            'class': 'form-control',
            'maxlength': '254',
        })
    )

    instituicao = forms.ModelChoiceField(
        queryset=Instituicao.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        empty_label='Selecione uma instituição'
    )

    # Campo único para DDD + número (ex: '(11) 99613-5479')
    telefone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: (11) 99613-5479',
            'class': 'form-control telefone-mask',
            'maxlength': '15',
            'inputmode': 'numeric',
            'pattern': r'\(\d{2}\) \d{5}-\d{4}',
            'title': 'Formato esperado: (AA) NNNNN-NNNN'
        })
    )

    class Meta:
        model = Usuario
        fields = ['nome', 'tipo', 'instituicao', 'nome_usuario', 'email', 'senha', 'telefone']

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

        # Salva o telefone já normalizado pelo `clean_telefone()` (form retorna o formato internacional)
        tel_input = self.cleaned_data.get('telefone')
        if tel_input:
            # o modelo irá normalizar novamente, mas guardamos o valor completo aqui
            usuario.telefone = tel_input

        # Salva o usuário e cria diretórios de mídia
        if commit:
            usuario.save()
            try:
                from .utils import create_user_dirs
                create_user_dirs(usuario)
            except Exception:
                pass  # não falha se não conseguir criar diretórios

        return usuario

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get('senha')
        senha_confirm = cleaned.get('senha_confirm')

        # check presence
        if not senha:
            raise ValidationError({'senha': 'Senha obrigatória.'})

        if senha_confirm is None:
            raise ValidationError({'senha_confirm': 'Confirmação de senha obrigatória.'})

        # check match
        if senha != senha_confirm:
            raise ValidationError({'senha_confirm': 'As senhas informadas não coincidem.'})

        # password complexity: min 8 chars, letters, digits and special char
        if len(senha) < 8:
            raise ValidationError({'senha': 'A senha deve ter no mínimo 8 caracteres.'})
        if not re.search(r'[A-Za-z]', senha):
            raise ValidationError({'senha': 'A senha deve conter ao menos uma letra.'})
        if not re.search(r'\d', senha):
            raise ValidationError({'senha': 'A senha deve conter ao menos um número.'})
        if not re.search(r'[^A-Za-z0-9]', senha):
            raise ValidationError({'senha': 'A senha deve conter ao menos um caractere especial.'})

        return cleaned

    def clean_telefone(self):
        tel = self.cleaned_data.get('telefone')
        if not tel:
            raise ValidationError('Telefone obrigatório. Informe no formato (AA) NNNNN-NNNN ou 11-13 dígitos.')
        # aceita formatos:
        #  - +CC (AA) NNNNN-NNNN
        #  - (AA) NNNNN-NNNN
        #  - 11..13 dígitos (opcional código do país + DDD + número)
        intl_pattern = re.compile(r"^\+\d{1,3} \(\d{2}\) \d{5}-\d{4}$")
        local_pattern = re.compile(r"^\(\d{2}\) \d{5}-\d{4}$")
        if intl_pattern.fullmatch(tel.strip()):
            return tel.strip()
        if local_pattern.fullmatch(tel.strip()):
            # assume país padrão +55 quando não informado
            return f"+55 {tel.strip()}"

        digits = re.sub(r'\D', '', tel)
        if len(digits) >= 11 and len(digits) <= 13:
            country = digits[:-11] if len(digits) > 11 else '55'
            core = digits[-11:]
            area = core[:2]
            local = core[2:]
            return f"+{country} ({area}) {local[:5]}-{local[5:]}"

        raise ValidationError('Telefone inválido. Formato exigido: +CC (AA) NNNNN-NNNN, (AA) NNNNN-NNNN ou 11-13 dígitos numéricos.')


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
    # Tornar email e telefone obrigatórios no formulário de edição
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Ex: voce@exemplo.com',
            'class': 'form-control',
            'maxlength': '254',
        })
    )
    
    instituicao = forms.ModelChoiceField(
        queryset=Instituicao.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        empty_label='Selecione uma instituição'
    )

    # Campo único para DDD + número (ex: '(11) 99613-5479' ou '11996135479')
    telefone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: (11) 99613-5479 ou 11996135479',
            'class': 'form-control telefone-mask',
            'maxlength': '15',
            'inputmode': 'numeric',
            'pattern': r'\(\d{2}\) \d{5}-\d{4}',
            'title': 'Formato esperado: (AA) NNNNN-NNNN'
        })
    )
    nova_senha = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Digite nova senha', 'class': 'form-control', 'id': 'id_senha'}),
        label="Nova senha"
    )

    class Meta:
        model = Usuario
        # remove 'senha' daqui, só campos de dados normais
        fields = ['nome', 'nome_usuario', 'email', 'instituicao', 'telefone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.telefone:
            tel = self.instance.telefone
            # já armazenamos o telefone no formato +CC (AA) NNNNN-NNNN
            # Ao editar no perfil, mostramos apenas (AA) NNNNN-NNNN (sem +CC)
            tel = tel.strip()
            m = re.match(r'^\+\d{1,3}\s*(\(\d{2}\)\s*\d{5}-\d{4})$', tel)
            if m:
                self.initial['telefone'] = m.group(1)
            else:
                # se não bater com o padrão internacional, tenta extrair a parte local
                digits = re.sub(r'\D', '', tel)
                if len(digits) >= 11:
                    core = digits[-11:]
                    area = core[:2]
                    local = core[2:]
                    self.initial['telefone'] = f"({area}) {local[:5]}-{local[5:]}"
                else:
                    # fallback: exibe o valor como está
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
        # Salva o telefone completo (clean_telefone retorna formato internacional)
        tel_input = self.cleaned_data.get('telefone')
        if tel_input:
            usuario.telefone = tel_input

        if commit:
            usuario.save()
        return usuario

    def clean_telefone(self):
        tel = self.cleaned_data.get('telefone')
        if not tel:
            raise ValidationError('Telefone obrigatório. Informe no formato (AA) NNNNN-NNNN ou 11-13 dígitos.')
        pattern = re.compile(r"\(\d{2}\) \d{5}-\d{4}")
        if pattern.fullmatch(tel.strip()):
            return tel.strip()
        digits = re.sub(r'\D', '', tel)
        if len(digits) == 11:
            area = digits[:2]
            local = digits[2:]
            return f"({area}) {local[:5]}-{local[5:]}"
        raise ValidationError('Telefone inválido. Formato exigido: (AA) NNNNN-NNNN ou somente 11 dígitos numéricos.')

    def clean_nova_senha(self):
        nova = self.cleaned_data.get('nova_senha')
        if not nova:
            return nova
        # enforce complexity: min 8 chars, letter, digit, special
        if len(nova) < 8:
            raise ValidationError('A nova senha deve ter no mínimo 8 caracteres.')
        if not re.search(r'[A-Za-z]', nova):
            raise ValidationError('A nova senha deve conter ao menos uma letra.')
        if not re.search(r'\d', nova):
            raise ValidationError('A nova senha deve conter ao menos um número.')
        if not re.search(r'[^A-Za-z0-9]', nova):
            raise ValidationError('A nova senha deve conter ao menos um caractere especial.')
        return nova

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
