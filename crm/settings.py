INSTALLED_APPS = [
    # Default Django apps...
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Your app(s)
    "crm",
    
    # Add django-crontab
    "django_crontab",
    "django_celery_beat",

]

# ============================================
# Cron job configuration — runs every 5 minutes
# ============================================
CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]

# =========================================
# Celery configuration
# =========================================
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
accept_content = ['json']
timezone = 'UTC'

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.task.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0) #Every mondy at 6am
    },
}


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # add template dirs if any
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


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # must be before auth
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # required
    'django.contrib.messages.middleware.MessageMiddleware',    # required
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]



