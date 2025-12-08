
"""
Configurações do projeto Django instituicao_ensino.

Inclui carregamento de variáveis de ambiente, configuração de apps, middlewares, banco de dados,
arquivos estáticos, internacionalização, email e outras opções essenciais para o funcionamento do sistema.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------
# Simple .env loader (key=value per line) for local dev convenience
# Looks for .env in project folder and repository root (next to README.md)
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Função utilitária para carregar variáveis de ambiente de um arquivo .env
# -------------------------------------------------------------------
def _load_env_file(path):
    """
    Carrega variáveis de ambiente de um arquivo .env (key=value por linha).
    Ignora linhas comentadas ou inválidas.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        # ignore env file parse errors silently for dev
        pass

env_candidates = [
    os.path.join(BASE_DIR, '.env'),            # project folder
    os.path.join(BASE_DIR.parent, '.env'),     # repo root (next to README.md)
]
for env_path in env_candidates:
    if os.path.exists(env_path):
        _load_env_file(env_path)
        break



# -------------------------------------------------------------------
# Configuração de arquivos de mídia (uploads de usuários)
# -------------------------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Cria a pasta de mídia ao importar settings, se não existir
try:
    os.makedirs(MEDIA_ROOT, exist_ok=True)
except Exception:
    # Não interrompe a importação se não conseguir criar a pasta
    pass



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-@iaeholp9_yn05zfxj%kluqxz!&-1kbf#gd0_s5g-v-c8#d3-r"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]



# -------------------------------------------------------------------
# Definição das aplicações instaladas
# -------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'usuarios',
    'eventos',
    'rest_framework',
    'rest_framework.authtoken',
    'instituicao_ensino',
    'notifications',
]

    
# -------------------------------------------------------------------
# Configuração do Django REST Framework (API authentication + throttling)
# -------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Throttle rates are referenced by scope names in custom throttles
    'DEFAULT_THROTTLE_RATES': {
        'event_list': '20/day',
        'event_register': '50/day',
    }
}


# -------------------------------------------------------------------
# Middlewares do projeto
# -------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware", 
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "instituicao_ensino.middleware.AuditMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# -------------------------------------------------------------------
# Configuração de URLs, templates e WSGI
# -------------------------------------------------------------------
ROOT_URLCONF = "instituicao_ensino.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'instituicao_ensino', 'templates'),],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "instituicao_ensino.context_processors.global_nav",
            ],
        },
    },
]

WSGI_APPLICATION = "instituicao_ensino.wsgi.application"



# -------------------------------------------------------------------
# Configuração do banco de dados
# -------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}



# -------------------------------------------------------------------
# Validação de senha
# -------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]



# -------------------------------------------------------------------
# Internacionalização e fuso horário
# -------------------------------------------------------------------

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True



# -------------------------------------------------------------------
# Arquivos estáticos (CSS, JS, imagens)
# -------------------------------------------------------------------

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# -------------------------------------------------------------------
# Tipo de campo primário padrão para modelos
# -------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Configuração de email
# -------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'SGEA <no-reply@sgea.local>')

# URL pública do site usada em emails e QR codes (definida no .env para produção)
SITE_URL = os.environ.get('SITE_URL', '')
