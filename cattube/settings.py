import os
from urllib.parse import urlparse
from urllib.parse import urlunparse

from django.core.exceptions import ImproperlyConfigured
# Never put credentials in your code!
from dotenv import load_dotenv

load_dotenv()

REQUIRED_ENV_VARS = (
    'WEB_APPLICATION_HOST',
    'B2_APPLICATION_KEY_ID',
    'B2_APPLICATION_KEY',
    'B2_BUCKET_NAME',
    'B2_REGION',
    'B2_PUBLIC_URL_BASE',
    'TRANSLOADIT_KEY',
    'TRANSLOADIT_SECRET',
    'TRANSLOADIT_TEMPLATE_ID',
)


def _require_env_vars(environ=os.environ):
    missing = [name for name in REQUIRED_ENV_VARS if not environ.get(name)]
    if missing:
        raise ImproperlyConfigured(
            'Missing required environment variables: ' + ', '.join(missing)
        )


def _normalize_public_url_base(value):
    public_url_base = value.strip().rstrip('/')
    if '://' not in public_url_base:
        public_url_base = f'https://{public_url_base}'

    parsed = urlparse(public_url_base)
    if parsed.scheme != 'https' or not parsed.netloc:
        raise ImproperlyConfigured('B2_PUBLIC_URL_BASE must be an https:// URL with a host.')
    if parsed.query or parsed.fragment:
        raise ImproperlyConfigured('B2_PUBLIC_URL_BASE must not include a query string or fragment.')

    path = parsed.path.rstrip('/')
    return urlunparse((parsed.scheme, parsed.netloc, path, '', '', ''))


_require_env_vars()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '9tf$jps6u-rxnv8nuur=*z&44$d!*_k@9td4jfaurtd5)xu_50'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [os.environ['WEB_APPLICATION_HOST']]

CSRF_TRUSTED_ORIGINS = list(map(lambda host: f'https://{host}', ALLOWED_HOSTS))

# Required for ngrok and other proxies that terminate TLS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'storages',

    'cattube.core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cattube.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'cattube/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cattube.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'cattube/static'),
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# Set these in a .env file or as environment variables.
B2_APPLICATION_KEY_ID = os.environ['B2_APPLICATION_KEY_ID']
B2_APPLICATION_KEY = os.environ['B2_APPLICATION_KEY']
B2_BUCKET_NAME = os.environ['B2_BUCKET_NAME']
B2_REGION = os.environ['B2_REGION']
B2_STORAGE_ENDPOINT_URL = f'https://s3.{B2_REGION}.backblazeb2.com'
B2_PUBLIC_URL_BASE = _normalize_public_url_base(os.environ['B2_PUBLIC_URL_BASE'])

# django-storages calls this custom_domain, but it may include a path prefix.
B2_PUBLIC_URL_CUSTOM_DOMAIN = B2_PUBLIC_URL_BASE.removeprefix('https://')

B2_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

B2_STATIC_LOCATION = 'static'
STATICFILES_STORAGE = 'cattube.storage_backends.StaticStorage'
STATIC_URL = f'{B2_PUBLIC_URL_BASE}/static/'

TRANSLOADIT_KEY = os.environ['TRANSLOADIT_KEY']
TRANSLOADIT_SECRET = os.environ['TRANSLOADIT_SECRET']
TRANSLOADIT_TEMPLATE_ID = os.environ['TRANSLOADIT_TEMPLATE_ID']
