import logging
import os
import zipfile
from datetime import datetime
from pathlib import Path

from django.conf import settings


logger = logging.getLogger(__name__)


EXCLUDED_DIRECTORIES = {
    "backups",
    "__pycache__",
    ".git",
    ".venv",
    "env",
    "venv",
    "node_modules",
}


def create_backup_archive(
    destination: Path,
    *,
    source_dir=None,
    database_path=None,
) -> Path:
    """Archive application files and the database configured for this deployment."""

    logger.info("Начало создания резервной копии")

    destination.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_path = destination / f"full_backup_{timestamp}.zip"

    base_dir = Path(source_dir or settings.BASE_DIR)

    logger.debug(
        "Параметры резервного копирования: source=%s, destination=%s",
        base_dir,
        destination,
    )

    files_count = 0

    try:
        with zipfile.ZipFile(
            archive_path,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as archive:

            for root, directories, files in os.walk(base_dir):
                directories[:] = [
                    item
                    for item in directories
                    if item not in EXCLUDED_DIRECTORIES
                ]

                root_path = Path(root)

                for filename in files:
                    file_path = root_path / filename

                    archive.write(
                        file_path,
                        file_path.relative_to(base_dir),
                    )

                    files_count += 1

        logger.debug(
            "Файлы приложения добавлены в архив: %s",
            files_count,
        )

        database_path = Path(
            database_path
            or settings.DATABASES["default"]["NAME"]
        )

        logger.debug(
            "Проверка базы данных для включения в резервную копию: %s",
            database_path,
        )

        if (
            database_path.exists()
            and not database_path.is_relative_to(base_dir)
        ):
            with zipfile.ZipFile(
                archive_path,
                "a",
                zipfile.ZIP_DEFLATED,
            ) as archive:
                archive.write(
                    database_path,
                    Path("database") / database_path.name,
                )

            logger.debug(
                "База данных добавлена в архив: %s",
                database_path,
            )

        elif database_path.exists():
            logger.debug(
                "База данных уже находится внутри исходного каталога: %s",
                database_path,
            )

        else:
            logger.warning(
                "Файл базы данных не найден и не был добавлен: %s",
                database_path,
            )

    except Exception:
        logger.exception(
            "Ошибка при создании резервной копии: %s",
            archive_path,
        )

        # Если архив создался частично, удаляем его,
        # чтобы не оставить повреждённый backup.
        try:
            if archive_path.exists():
                archive_path.unlink()
                logger.debug(
                    "Удалён повреждённый архив резервной копии: %s",
                    archive_path,
                )
        except Exception:
            logger.exception(
                "Не удалось удалить повреждённый архив: %s",
                archive_path,
            )

        raise

    logger.info(
        "Резервная копия успешно создана: %s, файлов: %s",
        archive_path,
        files_count,
    )

    return archive_path