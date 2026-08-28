import os
import zipfile
from datetime import datetime
from pathlib import Path

from django.conf import settings


EXCLUDED_DIRECTORIES = {"backups", "__pycache__", ".git", ".venv", "env", "venv", "node_modules"}


def create_backup_archive(destination: Path, *, source_dir=None, database_path=None) -> Path:
    """Archive application files and the database configured for this deployment."""
    destination.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_path = destination / f"full_backup_{timestamp}.zip"
    base_dir = Path(source_dir or settings.BASE_DIR)

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, directories, files in os.walk(base_dir):
            directories[:] = [item for item in directories if item not in EXCLUDED_DIRECTORIES]
            root_path = Path(root)
            for filename in files:
                file_path = root_path / filename
                archive.write(file_path, file_path.relative_to(base_dir))

        database_path = Path(database_path or settings.DATABASES["default"]["NAME"])
        if database_path.exists() and not database_path.is_relative_to(base_dir):
            archive.write(database_path, Path("database") / database_path.name)

    return archive_path
