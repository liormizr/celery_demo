from argparse import ArgumentParser

from celery_demo.commands import purge, apply_async_workflow, monitor


def main():
    args = parser_command_line_args()
    if args.purge:
        return purge()

    workflow_async_result = apply_async_workflow(
        args.workflow_cycle_count,
        args.operation_concurrent_count)
    if args.monitor:
        monitor(workflow_async_result)


def parser_command_line_args():
    parser = ArgumentParser(prog='Celery Demo CLI')
    parser.add_argument(
        '--cycle-count',
        default=1,
        type=int,
        dest='workflow_cycle_count',
        help='Number of times that the demo workflow will repeat',
    )
    parser.add_argument(
        '--operation-concurrent',
        default=1,
        type=int,
        dest='operation_concurrent_count',
        help='Number of operation tasks in one workflow cycle',
    )
    parser.add_argument(
        '--purge',
        action='store_true',
        help="Purge all working and schedule workflow's",
    )
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Monitor progress',
    )
    return parser.parse_args()


if __name__ == '__main__':
    main()
