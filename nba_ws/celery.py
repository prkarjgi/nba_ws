"""Module used to handle Celery setup.

Instantiation of Celery object used in the application, setting up celery
configs and the celery beat scheduling settings.
"""
import os

from celery import Celery
from celery.schedules import crontab

from nba_ws.common.util import TwitterOAuth2

celery = Celery('nba_ws')

celery.config_from_object(os.getenv('CELERY_CONFIG'))

oauth = TwitterOAuth2()
celery.conf.beat_schedule = {
    'get-data-periodic': {
        'task': 'nba_ws.tasks.get_data_periodic',
        'schedule': crontab(minute=0, hour='*/2'),
        'args': (oauth.bearer_token,)
    },
}
