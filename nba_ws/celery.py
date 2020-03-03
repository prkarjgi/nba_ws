from celery import Celery
import os

celery = Celery('nba_ws')

celery.config_from_object(os.getenv('CELERY_CONFIG'))
