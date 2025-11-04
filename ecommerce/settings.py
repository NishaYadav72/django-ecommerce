"""
Django settings for ecommerce project (Render ready).
"""

from pathlib import Path
import os
import dj_database_url
from django.contrib.auth import get_user_model

# ----------------------------------------------------
# BASE DIRECTORY
# ----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------------------------------------
# SECURITY CONFIG
# ----------------------------------------------------
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-n(+_ybfqlbz8*lycwtk_me_wcv26r6dmf2fd8%hh@2na)k^vo0'
)

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    'django-ecommerce-1xov.onrender.com',
    '127.0.0.1',
    'localhost'
]

# ----------------------------------------------------
# APPLICATIONS
# ----------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'core',
]

# ----------------------------------------------------
# MIDDLEWARE
# ----------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ For static files on Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecommerce.urls'

AUTH_USER_MODEL = 'core.ZeUser'

# ----------------------------------------------------
# TEMPLATES
# ----------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # ✅ global templates folder
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

WSGI_APPLICATION = 'ecommerce.wsgi.application'

# ----------------------------------------------------
# DATABASE
# ----------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ✅ Render par agar DATABASE_URL set hai to PostgreSQL use karega
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(
        default=os.environ['DATABASE_URL'],
        conn_max_age=600,
    )

# ----------------------------------------------------
# PASSWORD VALIDATION
# ----------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ----------------------------------------------------
# INTERNATIONALIZATION
# ----------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ----------------------------------------------------
# STATIC & MEDIA FILES
# ----------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ----------------------------------------------------
# AUTH SETTINGS
# ----------------------------------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ----------------------------------------------------
# DEFAULT PK FIELD TYPE
# ----------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ----------------------------------------------------
# AUTO CREATE SUPERUSER ON RENDER DEPLOY
# ----------------------------------------------------
if os.environ.get('RENDER_SUPERUSER_EMAIL'):
    try:
        User = get_user_model()
        email = os.environ['RENDER_SUPERUSER_EMAIL']
        if not User.objects.filter(email=email).exists():
            print("⚙️ Creating superuser automatically...")
            User.objects.create_superuser(
                username=os.environ['RENDER_SUPERUSER_USERNAME'],
                email=email,
                password=os.environ['RENDER_SUPERUSER_PASSWORD']
            )
    except Exception as e:
        print(f"⚠️ Superuser creation failed: {e}")
