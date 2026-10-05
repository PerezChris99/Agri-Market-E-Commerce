
from pathlib import Path
import os
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
DEBUG = os.environ.get('DJANGO_DEBUG', os.environ.get('DEBUG', 'False')).strip().lower() in {'1', 'true', 'yes', 'on'}

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-local-development-only'
    else:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY must be set when DEBUG=False')

ALLOWED_HOSTS = [host.strip() for host in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Our installed apps
    'store.apps.StoreConfig',
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

ROOT_URLCONF = 'ecommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.cart_data',
                'store.context_processors.categories',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecommerce.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
if not DEBUG and not DATABASE_URL:
    raise ImproperlyConfigured('DATABASE_URL must be set when DEBUG=False')

if DATABASE_URL:
    try:
        import dj_database_url
        DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG)}
    except ImportError as exc:
        raise ImproperlyConfigured('dj-database-url is required when DATABASE_URL is configured') from exc
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'agrimarket.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Kampala'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Authentication settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# PayPal settings - KEEP THESE SECRET IN PRODUCTION
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '')
PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')  # 'sandbox' or 'live'

# Session settings
SESSION_COOKIE_AGE = 86400 * 14  # 14 days
SESSION_SAVE_EVERY_REQUEST = True

# Security settings for production
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    SECURE_SSL_REDIRECT = False

# Messages framework
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'


# ============================================
# MOBILE MONEY PAYMENT SETTINGS (Uganda)
# ============================================

# MTN Mobile Money API (MTN MoMo)
# Get credentials from: https://momodeveloper.mtn.com/
MTN_MOMO_API_USER = os.environ.get('MTN_MOMO_API_USER', '')
MTN_MOMO_API_KEY = os.environ.get('MTN_MOMO_API_KEY', '')
MTN_MOMO_SUBSCRIPTION_KEY = os.environ.get('MTN_MOMO_SUBSCRIPTION_KEY', '')
MTN_MOMO_ENVIRONMENT = os.environ.get('MTN_MOMO_ENVIRONMENT', 'sandbox')  # 'sandbox' or 'production'
MTN_MOMO_CALLBACK_URL = os.environ.get('MTN_MOMO_CALLBACK_URL', 'https://yourdomain.com/api/momo/callback/')
MTN_MOMO_CURRENCY = 'UGX'

# Airtel Money API
# Get credentials from: https://developers.airtel.africa/
AIRTEL_CLIENT_ID = os.environ.get('AIRTEL_CLIENT_ID', '')
AIRTEL_CLIENT_SECRET = os.environ.get('AIRTEL_CLIENT_SECRET', '')
AIRTEL_ENVIRONMENT = os.environ.get('AIRTEL_ENVIRONMENT', 'sandbox')  # 'sandbox' or 'production'
AIRTEL_CALLBACK_URL = os.environ.get('AIRTEL_CALLBACK_URL', 'https://yourdomain.com/api/momo/callback/')
AIRTEL_COUNTRY_CODE = 'UG'
AIRTEL_CURRENCY = 'UGX'

# Flutterwave Payment Gateway (Unified)
# Get credentials from: https://dashboard.flutterwave.com/
FLUTTERWAVE_PUBLIC_KEY = os.environ.get('FLUTTERWAVE_PUBLIC_KEY', '')
FLUTTERWAVE_SECRET_KEY = os.environ.get('FLUTTERWAVE_SECRET_KEY', '')
FLUTTERWAVE_ENCRYPTION_KEY = os.environ.get('FLUTTERWAVE_ENCRYPTION_KEY', '')
FLUTTERWAVE_ENVIRONMENT = os.environ.get('FLUTTERWAVE_ENVIRONMENT', 'sandbox')
FLUTTERWAVE_REDIRECT_URL = os.environ.get('FLUTTERWAVE_REDIRECT_URL', 'https://yourdomain.com/checkout/complete/')
FLUTTERWAVE_WEBHOOK_SECRET_HASH = os.environ.get('FLUTTERWAVE_WEBHOOK_SECRET_HASH', '')
MOMO_WEBHOOK_SECRET = os.environ.get('MOMO_WEBHOOK_SECRET', '')

# Payment provider preference
# Options: 'direct' (use MTN/Airtel APIs directly) or 'flutterwave' (use Flutterwave as unified gateway)
MOBILE_MONEY_PROVIDER = os.environ.get('MOBILE_MONEY_PROVIDER', 'flutterwave')


# ============================================
# SMS NOTIFICATION SETTINGS
# ============================================

# SMS Provider: 'africastalking' or 'twilio'
SMS_PROVIDER = os.environ.get('SMS_PROVIDER', 'africastalking')

# Africa's Talking SMS API
# Get credentials from: https://africastalking.com/
AT_USERNAME = os.environ.get('AT_USERNAME', 'sandbox')
AT_API_KEY = os.environ.get('AT_API_KEY', '')
AT_SENDER_ID = os.environ.get('AT_SENDER_ID', 'AgriMarket')

# Twilio SMS API (Alternative)
# Get credentials from: https://www.twilio.com/
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')


# ============================================
# WHATSAPP BUSINESS API SETTINGS
# ============================================

# WhatsApp Business API (via Meta/Facebook)
# Get credentials from: https://developers.facebook.com/docs/whatsapp/cloud-api/
WHATSAPP_PHONE_ID = os.environ.get('WHATSAPP_PHONE_ID', '')
WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN', 'agrimarket_verify_token')
WHATSAPP_BUSINESS_ACCOUNT_ID = os.environ.get('WHATSAPP_BUSINESS_ACCOUNT_ID', '')


# ============================================
# DELIVERY & LOGISTICS SETTINGS
# ============================================

# Default delivery fee (UGX) for within Kampala
DEFAULT_DELIVERY_FEE = int(os.environ.get('DEFAULT_DELIVERY_FEE', '5000'))

# Free delivery threshold (UGX)
FREE_DELIVERY_THRESHOLD = int(os.environ.get('FREE_DELIVERY_THRESHOLD', '100000'))

# Delivery time slots
DELIVERY_TIME_SLOTS = [
    ('morning', '8:00 AM - 12:00 PM'),
    ('afternoon', '12:00 PM - 4:00 PM'),
    ('evening', '4:00 PM - 8:00 PM'),
]


# ============================================
# CURRENCY & LOCALIZATION
# ============================================

# Default currency
DEFAULT_CURRENCY = 'UGX'
CURRENCY_SYMBOL = 'UGX '

# Exchange rates (approximate, for PayPal conversion)
USD_TO_UGX_RATE = int(os.environ.get('USD_TO_UGX_RATE', '3700'))


# ============================================
# SITE INFORMATION
# ============================================

SITE_NAME = 'Agri-Market Uganda'
SITE_TAGLINE = 'Fresh Farm Produce, Delivered to Your Door'
SITE_DESCRIPTION = 'Uganda\'s Premier Online Marketplace for Fresh Agricultural Products'
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'support@agrimarket.ug')
SUPPORT_PHONE = os.environ.get('SUPPORT_PHONE', '+256 700 000 000')
SUPPORT_WHATSAPP = os.environ.get('SUPPORT_WHATSAPP', '+256 700 000 000')


# ============================================
# LOGGING
# ============================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'agrimarket.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'store': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)