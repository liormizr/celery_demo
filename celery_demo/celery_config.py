""" Celery Configuration File
- Setup Celery application named "celery_demo",
- Create celery_demo celery logger,
- Load all tasks,
"""
import os
from kombu import Queue
from celery import Celery
from celery.utils.log import get_task_logger
from multiprocessing import cpu_count

# Celery broker
BROKER_HOST = os.getenv('BROKER_HOST', 'localhost')
BROKER_PORT = os.getenv('BROKER_PORT', '26379')
BROKER_URL = 'redis://{0}:{1}/0'.format(BROKER_HOST, BROKER_PORT)
CELERY_RESULT_BACKEND_URL = 'redis://{0}:{1}?new_join=1'.format(BROKER_HOST, BROKER_PORT)
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 60*30}

# Celery Queues
INGEST_QUEUE_NAME = INGEST_ROUTING_KEY = 'ingest'
OPERATION_QUEUE_NAME = OPERATION_ROUTING_KEY = 'operation'
DEFAULT_QUEUE_NAME = DEFAULT_ROUTING_KEY = DEFAULT_EXCHANGE = 'default'

# Celery tasks per queue
INGEST_QUEUE_TASKS = (
    'celery_demo.tasks.validate_system_task',
)
OPERATION_QUEUE_TASKS = (
    'celery_demo.tasks.operation_task',
)
DEFAULT_QUEUE_TASKS = (
    'celery_demo.tasks.create_workflow_task',
    'celery_demo.tasks.operation_summery_task',
    'celery_demo.tasks.cleanup_task',
)


def get_worker_count():
    """Return number of workers to start"""
    if os.getenv('CELERY_TASK') == 'operation':
        return cpu_count()
    return 1


class CeleryDemoRouter(object):
    def route_for_task(self, task, args=None, kwargs=None):
        if task in INGEST_QUEUE_TASKS:
            return {'exchange': DEFAULT_EXCHANGE, 'routing_key': INGEST_ROUTING_KEY}
        if task in OPERATION_QUEUE_TASKS:
            return {'exchange': DEFAULT_EXCHANGE, 'routing_key': OPERATION_ROUTING_KEY}
        if task in DEFAULT_QUEUE_TASKS:
            return {'exchange': DEFAULT_EXCHANGE, 'routing_key': DEFAULT_ROUTING_KEY}
        return {'exchange': DEFAULT_EXCHANGE, 'routing_key': DEFAULT_ROUTING_KEY}


app = Celery('celery_demo')
app.conf.update(
    BROKER_URL=BROKER_URL,
    CELERY_RESULT_BACKEND=CELERY_RESULT_BACKEND_URL,
    CELERYD_PREFETCH_MULTIPLIER=1,
    CELERYD_CONCURRENCY=get_worker_count(),
    CELERY_TASK_SERIALIZER='pickle',
    CELERY_ACCEPT_CONTENT=['pickle'],
    CELERY_ROUTES=['celery_demo.celery_config.CeleryDemoRouter'],
    CELERY_QUEUES=(
        Queue(DEFAULT_QUEUE_NAME, routing_key=DEFAULT_ROUTING_KEY),
        Queue(INGEST_QUEUE_NAME, routing_key=INGEST_ROUTING_KEY),
        Queue(OPERATION_QUEUE_NAME, routing_key=OPERATION_ROUTING_KEY),
    ),
    CELERY_DEFAULT_EXCHANGE=DEFAULT_EXCHANGE,
    CELERY_DEFAULT_QUEUE=DEFAULT_QUEUE_NAME,
    CELERY_DEFAULT_ROUTING_KEY=DEFAULT_ROUTING_KEY,
    CELERY_TRACK_STARTED=True,
)

logger = get_task_logger('celery_demo')

# This import must be placed at the end, after the app is defined
# otherwise we will get an import error in tasks module
import tasks
