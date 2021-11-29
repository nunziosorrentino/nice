"""
Django settings for virgo_glitches project.

Generated by 'django-admin startproject' using Django 3.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import environ
#from .base import *
import sys
sys.path.append("/var/www/html/reinforce/virgo_glitches")
sys.path.append("/var/www/html/reinforce/virgo_glitches/utilities")
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

env = environ.Env()
# reading .env file
environ.Env.read_env()

# SECURITY WARNING: keep the secret key used in production secret!
#WARNING: ADD this key to environ.

SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
#DEBUG = False


ALLOWED_HOSTS = ['ep-dev.ego-gw.eu', 'cmplwebtest']


# Application definition

INSTALLED_APPS = [
    'monitor.apps.MonitorConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

ROOT_URLCONF = 'virgo_glitches.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'virgo_glitches.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

#seetings for slwebtest3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env("DATABASE_NAME"),
        'USER': env("DATABASE_USER"),
        'PASSWORD': env("DATABASE_PASSWORD"),
        'HOST': env("DATABASE_HOST"),
        'PORT': env("DATABASE_PORT"),
        },
    'O2': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env("STAGINGDB_NAME_O2"),
        'USER': env("STAGINGDB_USER"),
        'PASSWORD': env("STAGINGDB_PASSWORD"),
        'HOST': env("STAGINGDB_HOST"),
        'PORT': env("DATABASE_PORT"),
        },
    'O3a': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env("STAGINGDB_NAME_O3a"),
        'USER': env("STAGINGDB_USER"),
        'PASSWORD': env("STAGINGDB_PASSWORD"),
        'HOST': env("STAGINGDB_HOST"),
        'PORT': env("DATABASE_PORT"),
        },
    'O3b': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env("STAGINGDB_NAME_O3b"),
        'USER': env("STAGINGDB_USER"),
        'PASSWORD': env("STAGINGDB_PASSWORD"),
        'HOST': env("STAGINGDB_HOST"),
        'PORT': env("DATABASE_PORT"),
        },
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/


############# added to serve HTTPS ############################


# secure proxy SSL header and secure cookies
#SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
#SESSION_COOKIE_SECURE = True
#CSRF_COOKIE_SECURE = True

# session expire at browser close
#SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# wsgi scheme
#s.environ['wsgi.url_scheme'] = 'https'

###############################################################

STATIC_URL = '/static/'