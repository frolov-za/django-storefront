import tempfile
import zipfile
from pathlib import Path

from django.test import SimpleTestCase

from label_printer.services.backup import create_backup_archive


class BackupArchiveTests(SimpleTestCase):
    def test_includes_database_configured_outside_application_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            app_directory = root / "app"
            app_directory.mkdir()
            (app_directory / "application.txt").write_text("application")
            ignored_directory = app_directory / "__pycache__"
            ignored_directory.mkdir()
            (ignored_directory / "cache.pyc").write_text("cache")
            database_path = root / "data" / "storefront.sqlite3"
            database_path.parent.mkdir()
            database_path.write_text("database")

            archive_path = create_backup_archive(
                root / "backups", source_dir=app_directory, database_path=database_path
            )

            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {"application.txt", "database/storefront.sqlite3"},
                )
