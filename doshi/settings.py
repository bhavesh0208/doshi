from pathlib import Path
import os
import environ

myenv = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = myenv("SECRET_KEY")
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = myenv("DEBUG")

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "doshi.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "doshi.wsgi.application"
AUTH_USER_MODEL = "app.User"

AUTHENTICATION_BACKENDS = ["app.backends.EmailBackend"]

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": myenv("DB_ENGINE"),
        "NAME": myenv("DB_NAME"),
        "ENFORCE_SCHEMA": False,
        "CLIENT": {
            "host": myenv("MONGODB_HOST_URL"),
        },
    },
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_L10N = False

USE_TZ = True

STATIC_URL = "static/"

MEDIA_URL = "media/"

if DEBUG:
    STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
else:
    STATIC_ROOT = os.path.join(BASE_DIR, "static")
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# SMTP Configuration
DEFAULT_FROM_EMAIL = myenv("DEFAULT_FROM_EMAIL") 
EMAIL_BACKEND = myenv("EMAIL_BACKEND")
EMAIL_HOST = myenv("EMAIL_HOST")
EMAIL_PORT = myenv("EMAIL_PORT")
EMAIL_USE_TLS = True
EMAIL_HOST_USER = myenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = myenv("EMAIL_HOST_PASSWORD")

# OTP Configuration
OTP_EMAIL_TOKEN_VALIDITY = 300
OTP_EMAIL_BODY_TEMPLATE_PATH = os.path.join(
    BASE_DIR, "templates", "otp", "forgot_password_otp.html"
)
