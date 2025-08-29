# Docker окружение для courses_generator

Этот документ описывает настройку и использование Docker контейнера с PostgreSQL базой данных для проекта `courses_generator`.

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Python App    │    │   PostgreSQL    │    │     pgAdmin     │
│  (courses_env)  │◄──►│   (Docker)      │◄──►│   (Docker)      │
│                 │    │   Port: 5432    │    │   Port: 8080    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Требования

- Docker 27.5.1+
- docker-compose
- Python 3.7+
- 4GB+ свободной RAM
- 10GB+ свободного места на диске

## 🚀 Быстрый старт

### 1. Автоматический запуск

```bash
# Сделать скрипт исполняемым (если еще не сделано)
chmod +x build_and_run.sh

# Запустить сборку и запуск
./build_and_run.sh
```

### 2. Ручной запуск

```bash
# Сборка образа
docker-compose build

# Запуск контейнеров
docker-compose up -d

# Проверка статуса
docker-compose ps
```

## 📊 Компоненты

### PostgreSQL (courses_postgres)
- **Порт**: 5432
- **База данных**: courses_db
- **Пользователь**: courses_user
- **Пароль**: courses_password
- **Версия**: PostgreSQL 15 Alpine

### pgAdmin (courses_pgadmin)
- **Порт**: 8080
- **Email**: admin@courses.local
- **Пароль**: admin123
- **Версия**: pgAdmin 4

## 🗄️ Структура базы данных

### Основные таблицы

#### projects
- `id` - UUID первичный ключ
- `name` - Название проекта
- `description` - Описание
- `video_path` - Путь к видео
- `audio_path` - Путь к аудио
- `output_path` - Путь к результату
- `status` - Статус проекта
- `created_at` - Время создания
- `updated_at` - Время обновления

#### processing_tasks
- `id` - UUID первичный ключ
- `project_id` - Ссылка на проект
- `task_type` - Тип задачи
- `parameters` - JSON параметры
- `status` - Статус задачи
- `progress` - Прогресс (0-100)
- `error_message` - Сообщение об ошибке
- `started_at` - Время начала
- `completed_at` - Время завершения

#### results
- `id` - UUID первичный ключ
- `project_id` - Ссылка на проект
- `task_id` - Ссылка на задачу
- `file_path` - Путь к файлу
- `file_size` - Размер файла
- `duration_seconds` - Длительность
- `quality_metrics` - JSON метрики качества

#### settings
- `key` - Ключ настройки
- `value` - Значение
- `description` - Описание

### Представления

#### project_stats
Статистика по проектам с количеством задач и прогрессом.

## 🔧 Управление

### Основные команды

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Просмотр логов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f postgres
docker-compose logs -f pgadmin

# Обновление
docker-compose pull
docker-compose up -d
```

### Управление контейнерами

```bash
# Статус контейнеров
docker-compose ps

# Вход в контейнер PostgreSQL
docker exec -it courses_postgres psql -U courses_user -d courses_db

# Вход в контейнер pgAdmin
docker exec -it courses_pgadmin bash

# Остановка конкретного сервиса
docker-compose stop postgres
docker-compose start postgres
```

### Резервное копирование

```bash
# Создание бэкапа
docker exec courses_postgres pg_dump -U courses_user courses_db > backup.sql

# Восстановление из бэкапа
docker exec -i courses_postgres psql -U courses_user -d courses_db < backup.sql
```

## 🐍 Python интеграция

### Подключение к базе данных

```python
from database_client import DatabaseClient

# Создание клиента
db_client = DatabaseClient(
    host="localhost",
    port=5432,
    database="courses_db",
    user="courses_user",
    password="courses_password"
)

# Подключение
if db_client.connect():
    # Работа с базой данных
    projects = db_client.get_all_projects()
    print(f"Найдено проектов: {len(projects)}")
    
    # Отключение
    db_client.disconnect()
```

### Примеры использования

```python
# Создание проекта
from database_client import Project

project = Project(
    name="Мой проект",
    description="Описание проекта",
    video_path="/path/to/video.mp4",
    audio_path="/path/to/audio.mp3"
)

project_id = db_client.create_project(project)

# Создание задачи
from database_client import ProcessingTask

task = ProcessingTask(
    project_id=project_id,
    task_type="wav2lip_sync",
    parameters={"fps": 25, "img_size": 96}
)

task_id = db_client.create_task(task)

# Обновление прогресса
db_client.update_task_progress(task_id, 50, "processing")
```

## 🔍 Мониторинг

### Проверка здоровья

```bash
# Проверка PostgreSQL
docker exec courses_postgres pg_isready -U courses_user -d courses_db

# Проверка pgAdmin
curl -f http://localhost:8080 || echo "pgAdmin недоступен"
```

### Логи и отладка

```bash
# Логи PostgreSQL
docker-compose logs postgres

# Логи pgAdmin
docker-compose logs pgadmin

# Поиск ошибок
docker-compose logs | grep -i error
```

## 🚨 Устранение неполадок

### Частые проблемы

#### 1. Порт 5432 занят
```bash
# Проверка занятых портов
sudo netstat -tulpn | grep :5432

# Остановка локального PostgreSQL (если запущен)
sudo systemctl stop postgresql
```

#### 2. Недостаточно места на диске
```bash
# Проверка свободного места
df -h

# Очистка Docker
docker system prune -a
```

#### 3. Проблемы с правами доступа
```bash
# Проверка прав на файлы
ls -la

# Установка правильных прав
chmod 644 *.sql *.sh
chmod +x build_and_run.sh
```

#### 4. Контейнер не запускается
```bash
# Проверка логов
docker-compose logs

# Пересборка образа
docker-compose build --no-cache
docker-compose up -d
```

### Восстановление после сбоя

```bash
# Полная перезагрузка
docker-compose down --volumes --remove-orphans
docker-compose build --no-cache
docker-compose up -d
```

## 📈 Производительность

### Настройки PostgreSQL

```sql
-- Проверка текущих настроек
SHOW shared_buffers;
SHOW effective_cache_size;
SHOW work_mem;

-- Оптимизация для разработки
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
SELECT pg_reload_conf();
```

### Мониторинг ресурсов

```bash
# Использование памяти
docker stats

# Использование диска
docker system df

# Производительность PostgreSQL
docker exec courses_postgres psql -U courses_user -d courses_db -c "
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public';"
```

## 🔐 Безопасность

### Изменение паролей

```bash
# Изменение пароля PostgreSQL
docker exec -it courses_postgres psql -U courses_user -d courses_db -c "
ALTER USER courses_user PASSWORD 'новый_пароль';"

# Изменение пароля pgAdmin
docker exec -it courses_pgadmin python3 /pgadmin4/setup.py --user admin@courses.local --password новый_пароль
```

### Ограничение доступа

```bash
# Привязка к localhost только
# В docker-compose.yml изменить:
# ports:
#   - "127.0.0.1:5432:5432"
#   - "127.0.0.1:8080:80"
```

## 📚 Дополнительные ресурсы

- [PostgreSQL документация](https://www.postgresql.org/docs/)
- [pgAdmin документация](https://www.pgadmin.org/docs/)
- [Docker документация](https://docs.docker.com/)
- [docker-compose документация](https://docs.docker.com/compose/)

## 🤝 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs`
2. Убедитесь в корректности конфигурации
3. Проверьте системные требования
4. Создайте issue в репозитории проекта
