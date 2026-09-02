"""Celery entry points for maintenance work.

Task implementations intentionally delegate to application services so the
same workflows can be invoked and tested without a running Celery worker.
"""

from celery import shared_task

from label_printer.services.email import send_test_email
from label_printer.services.maintenance import (
    create_local_backup,
    remove_old_print_logs,
    send_backup_to_email,
    send_backup_to_telegram,
    send_daily_statistics,
    send_print_logs_by_email,
)


@shared_task
def send_daily_stats_to_telegram():
    return send_daily_statistics()


@shared_task
def delete_old_label_logs():
    return remove_old_print_logs()


@shared_task
def full_backup_local():
    return create_local_backup()


@shared_task
def full_backup_to_telegram():
    return send_backup_to_telegram()


@shared_task
def full_backup_to_email():
    return send_backup_to_email()


@shared_task
def send_logs_via_email():
    return send_print_logs_by_email()


def send_test_email_task(config_id):
    """Backward-compatible synchronous entry point used by the admin view."""
    return send_test_email(config_id)
