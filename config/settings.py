from pathlib import Path
import os
from django.contrib.messages import constants as messages
from decouple import config, Csv
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
#  CONFIGURACIÓN PRINCIPAL (Leyendo desde .env)
# =========================================================

# Seguridad: Si no hay .env, usa una clave default (solo para que no crashee en dev)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-clave-temporal-dev')

# Debug: Lee True/False desde el .env. Si no existe, asume False (Producción)
DEBUG = config('DEBUG', default=False, cast=bool)

# Hosts permitidos: Lee una lista separada por comas desde .env
# ALLOWED_HOSTS = config(
#    'ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

ALLOWED_HOSTS = ['punto-limpio.onrender.com', '127.0.0.1', 'localhost']

# Lista VIP de dominios confiables para formularios (Seguridad CSRF)
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

    # Apps de Terceros
    # (Aquí iría 'whitenoise' si fuera app, pero es middleware)

    # Apps Locales
    'apps.usuarios',
    'apps.core',
    'apps.servicios',
    'apps.inventario',
    'apps.finanzas',
]

# Debug Toolbar solo si estamos en modo DEBUG
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']


# =========================================================
#  MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    # 1. Debug Toolbar (Lo más arriba posible, solo en DEBUG)
    # Se inyecta dinámicamente abajo.

    'django.middleware.security.SecurityMiddleware',

    # 2. WhiteNoise (Justo después de Security para servir archivos estáticos)
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Middleware personalizado
    'apps.core.middleware.NoCacheMiddleware',
]

# Inyección condicional del Debug Toolbar
if DEBUG:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
# Configuración de IP interna para que se vea la barra
    INTERNAL_IPS = [
        "127.0.0.1",
    ]

ROOT_URLCONF = 'config.urls'

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
#  BASE DE DATOS
# =========================================================

# Usamos config() para leer del .env.
# Si estás en local y no has configurado DB en el .env, asegúrate de tener valores default
# o configura tu .env con estos datos.

# DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': config('DB_NAME', default='punto_limpio_db'),
#        'USER': config('DB_USER', default='postgres'),
#        'PASSWORD': config('DB_PASSWORD', default='root'),
#        'HOST': config('DB_HOST', default='localhost'),
#        'PORT': config('DB_PORT', default='5432'),
#    }
# }

if config('DATABASE_URL', default=None):
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True  # Obliga el uso de SSL en la nube para evitar cortes
        )
    }
else:
    # Si no existe DATABASE_URL (Significa que estamos en Local leyendo el .env)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT'),
        }
    }

# sobreescribe la configuración local automáticamente.
if config('DATABASE_URL', default=False):
    DATABASES['default'] = dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )

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

# Optimización de WhiteNoise para producción (compresión y caché)
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# =========================================================
#  OTRAS CONFIGURACIONES
# =========================================================

# Autenticación
AUTH_USER_MODEL = 'usuarios.Usuario'
LOGIN_REDIRECT_URL = 'core:tasks'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Mensajes
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'
MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# Configuración de correo (Usando config para leer del .env)
EMAIL_BACKEND = 'apps.core.email_backend.CustomEmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 5465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_TIMEOUT = 5
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')


# =========================================================
#  SEGURIDAD PARA PRODUCCIÓN (HTTPS)
# =========================================================

if not DEBUG:
    # Solo se activan si DEBUG es False (Servidor real)
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
else:
    # En local (Desarrollo)
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
