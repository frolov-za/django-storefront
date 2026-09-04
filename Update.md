# Docker Compose

Проект поддерживает два сценария сборки Docker-образа:

* **удалённая сборка** — исходный код берётся напрямую из GitHub;
* **локальная сборка** — исходный код берётся из локальной директории `./app`.

Для Django и Celery используется **один общий Docker-образ**. Сервисы `migrate`, `web`, `celery_beat` и `celery_worker` отличаются только запускаемой командой.

## Структура Docker-образов

Основное приложение использует образ:

```text
storefront:<branch>
```

Например:

```text
storefront:main
storefront:release
```

Для локальной сборки используется отдельный тег:

```text
storefront:local
```

Следующие сервисы используют один и тот же образ:

```text
migrate
web
celery_beat
celery_worker
```

Отдельные образы используются для:

```text
redis
nginx
```

---

## Удалённая сборка

Основной `docker-compose.yml` предназначен для удалённых хостов.

Исходный код берётся из репозитория:

```text
https://github.com/frolov-za/django-storefront
```

По умолчанию используется ветка `main`.

В Compose используется:

```yaml
build:
  context: https://github.com/frolov-za/django-storefront.git#${BRANCH:-main}
```

Поэтому, если переменная `BRANCH` не задана, используется:

```text
main
```

### Сборка из main

```bash
docker compose build app
```

После сборки запускаются сервисы:

```bash
docker compose up -d
```

В результате используется образ:

```text
storefront:main
```

### Сборка другой ветки

Ветка может быть переопределена через переменную `BRANCH`.

Например, для ветки `release`:

```bash
BRANCH=release docker compose build app
BRANCH=release docker compose up -d
```

В результате будет создан и использован образ:

```text
storefront:release
```

Другой пример:

```bash
BRANCH=develop docker compose build app
BRANCH=develop docker compose up -d
```

---

## Локальная сборка

Для локальной сборки используется отдельный файл:

```text
docker-compose.local.yml
```

В отличие от основного Compose-файла, он не обращается к GitHub. Исходный код берётся из:

```text
./app
```

Образ получает фиксированный тег:

```text
storefront:local
```

### Сборка

```bash
docker compose -f docker-compose.local.yml build app
```

### Запуск

```bash
docker compose -f docker-compose.local.yml up -d
```

Или сборка и запуск одной командой:

```bash
docker compose -f docker-compose.local.yml up -d --build
```

---

## Общий образ Django и Celery

Сервисы приложения используют один Docker-образ:

```yaml
image: storefront:local
```

для локальной сборки или:

```yaml
image: storefront:${BRANCH:-main}
```

для удалённой сборки.

Таким образом, Django и Celery не создают отдельные образы.

Логически схема выглядит следующим образом:

```text
                 ┌── migrate
                 │
                 ├── web
storefront:image ├── celery_beat
                 │
                 └── celery_worker
```

Это позволяет собрать зависимости и код проекта только один раз.

---

## Постоянные данные

Пользовательские и рабочие данные не должны храниться внутри Docker-образа.

Используются следующие директории/volumes:

```text
./data       → /app/data
./media      → /app/media
./logs       → /app/logs

static_volume    → /app/staticfiles
uwsgi-socket     → /tmp/uwsgi
redis-data       → /data
```

Особенно важно, что:

```text
./media
```

монтируется в контейнер как volume/bind mount.

Поэтому содержимое `media`, включая:

```text
media/product_images
```

не зависит от Docker-образа и сохраняется при пересоздании контейнера.

При сборке Docker `media/product_images` также не должен попадать в build context. Для этого директория исключается через `.dockerignore`:

```dockerignore
media/product_images/
```

---

## Обновление удалённого хоста

Для обновления приложения на удалённом сервере необходимо пересобрать image из нужной ветки и перезапустить сервисы.

Для `main`:

```bash
docker compose build app
docker compose up -d
```

Для `release`:

```bash
BRANCH=release docker compose build app
BRANCH=release docker compose up -d
```

При этом данные из:

```text
./data
./media
./logs
```

не входят в Docker-образ и сохраняются между обновлениями.

---

## Миграции

Миграции базы данных выполняются отдельным сервисом:

```text
migrate
```

Сервис `web` и Celery зависят от успешного завершения миграций.

Для `web`:

```yaml
depends_on:
  migrate:
    condition: service_completed_successfully
```

Для Celery:

```yaml
depends_on:
  migrate:
    condition: service_completed_successfully
```

Поэтому при запуске Compose сначала выполняются:

```bash
python manage.py migrate --noinput
```

и только после успешного завершения запускаются Django и Celery.

---

## Celery

В проекте используются два отдельных процесса Celery:

### Celery Beat

```text
celery_beat
```

Запускается командой:

```bash
celery -A storefront beat --loglevel=info
```

### Celery Worker

```text
celery_worker
```

Запускается командой:

```bash
celery -A storefront worker --loglevel=info
```

Оба процесса используют тот же Docker-образ, что и Django.

---

## Nginx

Nginx запускается из официального образа:

```text
nginx:alpine
```

Он получает доступ к:

```text
./media
./docs
static_volume
uwsgi-socket
```

Nginx является внешней точкой входа приложения и принимает HTTP/HTTPS-запросы на портах:

```text
80
443
```

---

## Redis

Redis запускается из:

```text
redis:7-alpine
```

Данные Redis сохраняются в Docker volume:

```text
redis-data
```

Redis доступен на порту:

```text
6379
```

---

## Краткая памятка

### Локальная разработка

```bash
docker compose -f docker-compose.local.yml up -d --build
```

### Удалённый сервер, ветка `main`

```bash
docker compose build app
docker compose up -d
```

### Удалённый сервер, ветка `release`

```bash
BRANCH=release docker compose build app
BRANCH=release docker compose up -d
```

### Посмотреть запущенные контейнеры

```bash
docker compose ps
```

### Посмотреть логи

```bash
docker compose logs -f web
```

Celery:

```bash
docker compose logs -f celery_worker
```

Celery Beat:

```bash
docker compose logs -f celery_beat
```

### Перезапустить приложение

```bash
docker compose restart web celery_worker celery_beat
```

### Остановить Compose

```bash
docker compose down
```

Команда `down` не удаляет именованные volumes, поэтому данные Redis и другие Docker volumes сохраняются.
