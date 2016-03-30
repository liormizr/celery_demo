from __future__ import print_function, division

import sys
from time import sleep
from itertools import chain
from collections import namedtuple

from celery.contrib.abortable import AbortableAsyncResult

from .tasks import validate_system_task, create_workflow_task, OperationTask
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
    # Block and wait for result.
    # If the remote call raised an exception,
    # Then that exception will be re-raised.
    validate_system_task.delay().get()

    ctx = {
        'workflow_cycle_count': workflow_cycle_count,
        'operation_concurrent_count': operation_concurrent_count,
    }
    async_workflow_result = create_workflow_task.apply_async(
        kwargs={'ctx': ctx})
    return async_workflow_result


def monitor(
        async_workflow_result,
        workflow_cycle_count,
        operation_concurrent_count):
    print('check out event monitoring with: '
          'celery -A celery_demo.celery_config events')
    print('See Flower http://localhost:5555')
    print('total operations count = {0} '
          '(workflow-cycles[{1}] * operation-concurrent[{2}])'.format(
            workflow_cycle_count * operation_concurrent_count,
            workflow_cycle_count, operation_concurrent_count))

    current_operation_intervals = 0
    total_operation_intervals = (
        workflow_cycle_count
        * operation_concurrent_count
        * OperationTask.TOTAL_PROGRESS_INTERVALS)

    for _ in xrange(workflow_cycle_count):
        workflow = async_workflow_result.get()['workflow']
        while workflow.status in ('PENDING', 'RECEIVED', 'STARTED'):
            progress = check_operations_progress(
                workflow,
                current_operation_intervals,
                total_operation_intervals)
            sys.stdout.write('\r                                           \r')
            sys.stdout.write(
                '\rProgress: {progress.percentage}%'.format(progress=progress))
            sys.stdout.flush()
            sleep(1)
        current_operation_intervals += progress.current_interval
        async_workflow_result = workflow

    sys.stdout.write('\n')
    sys.stdout.flush()


def check_operations_progress(async_result, current_interval, total_interval):
    for operation_task in async_result.parent.results:
        if operation_task.info is None:
            continue
        try:
            current_interval += operation_task.info['progress']
        except:
            if operation_task.status == 'SUCCESS':
                current_interval += OperationTask.TOTAL_PROGRESS_INTERVALS
    current_interval = min(current_interval, total_interval)

    return OperationsProgress(
        percentage=int(100 * current_interval / total_interval),
        current_interval=current_interval)

OperationsProgress = namedtuple(
    'OperationsProgress', 'percentage, current_interval')
