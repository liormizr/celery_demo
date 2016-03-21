"""
Celery Demo Tasks
We can see here 4 methods to create a celery task
1. unbind handler
2. bind handler
3. bind handler with a different celery Task class
4. creating and using a custom Task class
"""
from uuid import uuid4
from time import sleep
from celery import chain, chord
from celery.contrib.abortable import AbortableTask, ABORTED

from .celery_config import app, logger


# Basic task creation
@app.task
def validate_system_task():
    """validate_system_task celery task"""
    logger.info('starting to do some system validation')
    sleep(1)
    logger.info('did some system validation')


# binding the task handler to the task class
@app.task(bind=True)
def create_workflow_task(self, ctx):
    """create_workflow_task celery task
    :param self: celery task instance
    :param ctx: workflow state
    :type ctx: dict
    :return: dict(ctx, workflow)
    """
    assert ctx['workflow_cycle_count'] > 0, 'workflow_cycle_count have to be bigger then 0'
    assert ctx['operation_concurrent_count'] > 0, 'operation_concurrent_count have to be bigger then 0'

    logger.info('creating workflow')
    ctx.setdefault('workflow_count', 0)
    ctx['workflow_count'] += 1

    if ctx['workflow_count'] < ctx['workflow_cycle_count']:
        logger.info('need to repeat workflow')
        chord_callback_tasks = chain(
            operation_summery_task.subtask((), {'ctx': ctx}),
            create_workflow_task.subtask())
    else:
        logger.info('do not need to repeat workflow')
        chord_callback_tasks = chain(
            operation_summery_task.subtask((), {'ctx': ctx}),
            cleanup_task.subtask(()),
        )

    logger.info('workflow count: {ctx[workflow_count]}'.format(ctx=ctx))
    return {
        'ctx': ctx,
        'workflow': chord(
            operation_task.s(index=index, ctx=ctx)
            for index in xrange(ctx['operation_concurrent_count'])
        )(chord_callback_tasks),
    }


# binding the task handler to the task class
# switch between celery Task class to celery AbortableTask class
@app.task(bind=True, base=AbortableTask)
def operation_summery_task(self, operation_tasks_results, ctx):
    logger.info('Operation tasks results:')
    for index, result in enumerate(operation_tasks_results, 1):
        logger.info('[{index}]: {result},'.format(index=index, result=result))

    if self.is_aborted():
        logger.info('workflow is canceled or aborted... stopping')
        return ctx

    sleep(1)
    logger.info('doing summery')
    return ctx


@app.task
def cleanup_task(ctx):
    logger.info('Doing cleanup...')
    sleep(1)
    return ctx


class CeleryDemoTask(AbortableTask):
    """CeleryDemoTask is a custom Celery Task class
    This Class Documentation is from the Celery Task class code
    """
    def run(self, *args, **kwargs):
        """The body of the task executed by workers."""
        raise NotImplementedError('Tasks must define the run method.')

    def on_success(self, retval, task_id, args, kwargs):
        """Success handler.

        Run by the worker if the task executes successfully.

        :param retval: The return value of the task.
        :param task_id: Unique id of the executed task.
        :param args: Original arguments for the executed task.
        :param kwargs: Original keyword arguments for the executed task.

        The return value of this handler is ignored.

        """
        pass

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Retry handler.

        This is run by the worker when the task is to be retried.

        :param exc: The exception sent to :meth:`retry`.
        :param task_id: Unique id of the retried task.
        :param args: Original arguments for the retried task.
        :param kwargs: Original keyword arguments for the retried task.

        :keyword einfo: :class:`~billiard.einfo.ExceptionInfo`
                        instance, containing the traceback.

        The return value of this handler is ignored.

        """
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Error handler.

        This is run by the worker when the task fails.

        :param exc: The exception raised by the task.
        :param task_id: Unique id of the failed task.
        :param args: Original arguments for the task that failed.
        :param kwargs: Original keyword arguments for the task
                       that failed.

        :keyword einfo: :class:`~billiard.einfo.ExceptionInfo`
                        instance, containing the traceback.

        The return value of this handler is ignored.

        """
        pass

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Handler called after the task returns.

        :param status: Current task state.
        :param retval: Task return value/exception.
        :param task_id: Unique id of the task.
        :param args: Original arguments for the task that failed.
        :param kwargs: Original keyword arguments for the task
                       that failed.

        :keyword einfo: :class:`~billiard.einfo.ExceptionInfo`
                        instance, containing the traceback (if any).

        The return value of this handler is ignored.

        """
        pass


class OperationTask(CeleryDemoTask):
    name = '.'.join((__name__, 'operation_task'))
    TOTAL_PROGRESS_INTERVALS = 10

    def run(self, index, ctx):
        """ operation_task celery task
        :param index: operation index
        :type index: int
        :param ctx: workflow state
        :type ctx: dict
        """
        logger.info('Starting operation with args: index - {0}, ctx - {1}'.
                    format(index, ctx))
        try:
            general_workflow_index = ctx['workflow_count'] - 1 + index
            for progress in xrange(self.TOTAL_PROGRESS_INTERVALS):
                self.update_state(
                    state='PROGRESS' if not self.is_aborted() else ABORTED,
                    meta={
                        'progress': progress,
                        'total': self.TOTAL_PROGRESS_INTERVALS,
                        'index': general_workflow_index
                    })
                sleep(1)
                logger.info('in progress: {0}/{1}'.format(
                    progress, self.TOTAL_PROGRESS_INTERVALS))
        except:
            logger.exception('ERROR?')
            raise self.retry(
                kwargs={'index': index, 'ctx': ctx},
                countdown=60,
                max_retries=3)
        return {'index': index, 'ctx': ctx}
operation_task = OperationTask()
