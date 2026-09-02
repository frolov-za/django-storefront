"""Compatibility imports for the legacy management command."""

from label_printer.integrations.telegram import send_message as send_telegram_message
from label_printer.services.notifications import build_daily_volume_message as send_daily_volume_stats
