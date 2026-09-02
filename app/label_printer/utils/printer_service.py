"""Compatibility imports for code that has not moved to integrations yet."""

from label_printer.integrations.printers.diagnostics import (
    get_diagnostics as get_zpl_diagnostics,
    parse_zebra_hs_response,
    parse_zpl_help_output,
)
from label_printer.integrations.printers.transport import send_zpl as send_zpl_to_printer

__all__ = [
    "get_zpl_diagnostics",
    "parse_zebra_hs_response",
    "parse_zpl_help_output",
    "send_zpl_to_printer",
]
