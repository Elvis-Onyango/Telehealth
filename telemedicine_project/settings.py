import os
from pathlib import Path
from datetime import timedelta
from django.contrib.messages import constants as messages

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-=xae!($+ed7^lx@ew39n*d*ld6@tnwcv%vv@vyiy7m6r#oc&)8'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1']

# Application definition
INSTALLED_APPS = [
    # Third-party apps
    'webpush',
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'daphne',
    'channels',
    'admin_interface',
    'colorfield',
    'django_extensions',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'two_factor',
    'tailwind',
    'theme',


    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Local apps
    'apps.users',
    'apps.appointments',
    'apps.prescriptions',
    'apps.messaging',
    'apps.videoconferencing',
    'apps.notifications',
    'apps.landing',
    'apps.pharmacy',
    'apps.admin_auth',
]

# Custom Admin Panel Settings
ADMIN_SITE_HEADER = "Telemedicine Admin"
ADMIN_SITE_TITLE = "Telemedicine Dashboard"
ADMIN_INDEX_TITLE = "Welcome to the Telemedicine Admin Panel"

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'apps.users.middleware.ChatAccessMiddleware',
    "apps.admin_auth.middleware.SmartAdminLoginRedirectMiddleware",
]

ROOT_URLCONF = 'telemedicine_project.urls'


# Authentication backends
AUTHENTICATION_BACKENDS = (
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
)




REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication', 
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}


# Simple JWT settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# Push Notification Settings (using Firebase Cloud Messaging as example)
FCM_DJANGO_SETTINGS = {
    "FCM_SERVER_KEY": "[your-server-key]",
    "ONE_DEVICE_PER_USER": False,
    "DELETE_INACTIVE_DEVICES": True,
}


#Templates 


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Add global templates folder
        'APP_DIRS': True,  # Enables app-level templates
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

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Authentication settings
AUTH_USER_MODEL = 'users.User'
ACCOUNT_FORMS = {
    "signup": "apps.users.forms.CustomSignupForm",
    "login": "apps.users.forms.CustomLoginForm",
}



# WebSocket and Channels configuration
ASGI_APPLICATION = 'telemedicine_project.asgi.application'
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",  # Replace with Redis in production
    },
}

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'telemedicine',
        'USER': 'postgres',
        'PASSWORD': 'd8v34qn5',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
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

# Security settings
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]


#  login to your custom login page
LOGIN_URL = "/api/users/login-page/"  # This should match the URL for your custom  login page


SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# Static and media files
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Maximum upload size (50MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB

# Allowed file extensions
ALLOWED_VIDEO_EXTENSIONS = ['mp4', 'mov', 'avi', 'mkv']
ALLOWED_FILE_EXTENSIONS = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif']

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Site ID for allauth
SITE_ID = 1

# Tailwind configuration
TAILWIND_APP_NAME = 'theme'

# Messaging configuration (Twilio)
TWILIO_ACCOUNT_SID = "your_account_sid"
TWILIO_AUTH_TOKEN = "your_auth_token"
TWILIO_PHONE_NUMBER = "+your_twilio_number"

# MPESA API configuration
MPESA_ENV = "sandbox"
MPESA_CONSUMER_KEY = "your_consumer_key"
MPESA_CONSUMER_SECRET = "your_consumer_secret"
MPESA_SHORTCODE = "your_paybill_number"
MPESA_PASSKEY = "your_passkey"
MPESA_CALLBACK_URL = "https://yourdomain.com/mpesa/callback/"

# Message tags for Django messages framework
MESSAGE_TAGS = {
    messages.DEBUG: "gray",
    messages.INFO: "blue",
    messages.SUCCESS: "green",
    messages.WARNING: "yellow",
    messages.ERROR: "red",
}

# mail send

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Example for Gmail
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'onyangoelvis804@gmail.com'  # Your email address
EMAIL_HOST_PASSWORD = 'dazp lajb bzfh yudc'  # Your email password
DEFAULT_FROM_EMAIL = 'onyangoelvis804@gmail.com'  # Default sender email