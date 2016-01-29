"""
Django settings for Kobhio project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '&t3y$750-6atn949l3!rkjw#84346_hdi%%*3ekp#q2(ppbqs!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djangotoolbox',
    'permission_backend_nonrel',
    'import_export',
    'ikwen',

    #Third parties
    'ajaxuploader',

    'cms',
    'me',
    'movies',
    'reporting',
    'sales',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    'django.core.context_processors.request',
    # 'ikwen.context_processors.project_url',
)

ROOT_URLCONF = 'Shavida.urls'

WSGI_APPLICATION = 'Shavida.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django_mongodb_engine',
        'NAME': 'shavida',
    },
    'umbrella': {
        'ENGINE': 'django_mongodb_engine',
        'NAME': 'ikwen_umbrella',
    }
}

AUTH_USER_MODEL = 'ikwen.Member'

AUTHENTICATION_BACKENDS = (
    'permission_backend_nonrel.backends.NonrelPermissionBackend',
    'ikwen.backends.IkwenAuthBackend',
)

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = '/home/komsihon/Dropbox/PycharmProjects/Shavida/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/shavida/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '/home/komsihon/Dropbox/PycharmProjects/Shavida/static/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/shavida/static/'

TEMPLATE_DIRS = (os.path.join(BASE_DIR,  'templates'),)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': 60 * 9,
        'KEY_PREFIX': 'svdlocal',  # Use rather svdprod for Production
        'VERSION': '1'
    }
}

WEBSITE_NAME = 'Mixtel'

IKWEN_SERVICE_ID = ''

# Id of the member who runs this platform; typically a Content Vendor
PROVIDER_ID = ''

#
# IS_CONTENT_VENDOR = True
IS_VOD_OPERATOR = True

SALES_UNIT = "Volume"

CURRENCY = "XAF"

IKWEN_REGISTER_EVENTS = ('me.views.offer_welcome_bundle',)

LOGOUT_REDIRECT_URL = 'movies:home'

LOGIN_URL = 'ikwen:sign_in'

LOGIN_REDIRECT_URL = 'movies:home'

IKWEN_LOGIN_EVENTS = (
    'me.views.create_member_profile',
    'me.views.set_additional_session_info',
)

# Path of the function to execute when querying a file that is not in MP4. Your function will be called as such:
# your_function(request, media, *args, **kwargs)
# media is an instance of either Movie or SeriesEpisode.
# Your function can return either None (in this case the movies.stream() function will pursue its execution) or
# return a JSON error message of the form HttpResponse(json.dumps({'error': "Your error message"}))
NOT_MP4_HANDLER = 'movies.views.queue_for_transcode'
