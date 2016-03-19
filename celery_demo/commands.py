from __future__ import print_function

from itertools import chain
from uuid import uuid4
from celery.contrib.abortable import AbortableAsyncResult

from .tasks import validate_system_task, create_workflow_task
from . import celery_config


def purge():
    print('Cancelling all pending tasks')
    inspector = celery_config.app.control.inspect()
    for worker_tasks in chain(
            inspector.active().itervalues(),
            inspector.reserved().itervalues(),
            inspector.scheduled().itervalues()):
        for task in worker_tasks:
            try:
                print('Cancelling {task[id]}'.format(task=task))
                r = AbortableAsyncResult(task['id'])
                r.abort()
            except:
                print('Cannot abort task {task[id]}'.format(task=task))
    celery_config.app.control.purge()  # just in case we forgot something


def apply_async_workflow(workflow_cycle_count, operation_concurrent_count):
    validate_async_result = validate_system_task.delay()
    # Block and wait for result.
    # If the remote call raised an exception,
    # Then that exception will be re-raised.
    validate_async_result.get()

    ctx = {
        'workflow_cycle_count': workflow_cycle_count,
        'operation_concurrent_count': operation_concurrent_count,
    }
    return create_workflow_task.apply_async(
        kwargs={'ctx': ctx},
        task_id='workflow_0_{id}'.format(id=uuid4())
    )


def monitor(async_workflow_result):
    print('See Flower http://localhost:5555')
