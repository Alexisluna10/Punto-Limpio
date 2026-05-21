from pathlib import Path
import os
from django.contrib.messages import constants as messages
from decouple import config, Csv
import dj_database_url

# =========================================================
#  RUTAS BASE DEL PROYECTO
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
#  CONFIGURACIÓN PRINCIPAL Y SEGURIDAD NÚCLEO
# =========================================================
SECRET_KEY = config('SECRET_KEY', default='django-insecure-clave-temporal-dev')

# Debug: Por defecto es False (Producción)
DEBUG = config('DEBUG', default=False, cast=bool)

# Hosts permitidos
ALLOWED_HOSTS = ['punto-limpio.onrender.com', '127.0.0.1', 'localhost']

# Dominios confiables para formularios (Seguridad CSRF)
CSRF_TRUSTED_ORIGINS = [
    'https://punto-limpio.onrender.com',
]

# =========================================================
#  APLICACIONES
# =========================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps Locales
    'apps.usuarios',
    'apps.core',
    'apps.servicios',
    'apps.inventario',
    'apps.finanzas',

    # Apps de Terceros
    'anymail',
]

# =========================================================
#  MIDDLEWARE
# =========================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.NoCacheMiddleware',
]

ROOT_URLCONF = 'config.urls'

# =========================================================
#  TEMPLATES
# =========================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# =========================================================
#  BASE DE DATOS (Soporte Dual: Local y Nube)
# =========================================================
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    # Entorno Nube (Render / Supabase)
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True
        )
    }
else:
    # Entorno Local (.env)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# =========================================================
#  VALIDACIÓN DE PASSWORD
# =========================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =========================================================
#  IDIOMA Y ZONA HORARIA
# =========================================================
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# =========================================================
#  ARCHIVOS ESTÁTICOS Y MEDIA
# =========================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# =========================================================
#  CONFIGURACIONES DE USUARIO Y SESIÓN
# =========================================================
AUTH_USER_MODEL = 'usuarios.Usuario'
LOGIN_REDIRECT_URL = 'core:tasks'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# =========================================================
#  SISTEMA DE MENSAJERÍA
# =========================================================
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'
MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# =========================================================
#  CONFIGURACIÓN DE CORREO ELECTRÓNICO (Brevo)
# =========================================================
EMAIL_BACKEND = "anymail.backends.sendinblue.EmailBackend"
ANYMAIL = {
    "SENDINBLUE_API_KEY": config('BREVO_API_KEY', default=''),
}
DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER', default='puntolimpio039@gmail.com')

# =========================================================
#  SEGURIDAD PARA PRODUCCIÓN (HTTPS)
# =========================================================
EN_PRODUCCION = config('RENDER', default=False, cast=bool)

if EN_PRODUCCION:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False