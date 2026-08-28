"""Django admin registration entry point.

Registrations live next to the domain they administer; importing the modules
here keeps Django's standard autodiscovery behaviour unchanged.
"""

from label_printer import admin_notifications, admin_printers  # noqa: F401
