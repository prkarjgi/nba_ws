from celery import Celery

celery = Celery(
    'nba_news',
    broker='redis://localhost:6379/0'
)
