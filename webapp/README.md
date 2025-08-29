# 🌐 Courses Generator Web Application

Веб-приложение для управления проектами Wav2Lip с личным кабинетом, загрузкой файлов и интеграцией с базой данных.

## 🚀 Возможности

- **🔐 Аутентификация пользователей** - регистрация, вход, личный кабинет
- **📁 Управление проектами** - создание, редактирование, удаление
- **📤 Загрузка файлов** - видео и аудио файлы
- **⚙️ Обработка Wav2Lip** - запуск синхронизации
- **📊 Отслеживание прогресса** - мониторинг статуса задач
- **👑 Админ панель** - управление пользователями и проектами
- **🔒 Безопасность** - защита от несанкционированного доступа

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Веб-клиент   │    │   Flask App     │    │   PostgreSQL    │
│   (Browser)     │◄──►│   (Container)   │◄──►│   (Container)   │
│   Port: 5000    │    │   Port: 5000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Технологии

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Frontend**: Bootstrap 5, jQuery, Font Awesome
- **База данных**: PostgreSQL
- **Контейнеризация**: Docker, Docker Compose
- **Безопасность**: Werkzeug, хеширование паролей

## 📋 Требования

- Docker 27.5.1+
- docker-compose
- 4GB+ RAM
- 10GB+ свободного места

## 🚀 Быстрый старт

### 1. Запуск всех сервисов

```bash
# Из корневой директории проекта
docker-compose up -d

# Проверка статуса
docker-compose ps
```

### 2. Доступ к приложению

- **Веб-приложение**: http://localhost:5000
- **pgAdmin**: http://localhost:8080
- **PostgreSQL**: localhost:5432

### 3. Демо аккаунт

- **Администратор**: admin / admin123
- **Обычный пользователь**: зарегистрируйтесь через веб-интерфейс

## 📁 Структура проекта

```
webapp/
├── app.py                 # Основное Flask приложение
├── requirements.txt       # Python зависимости
├── Dockerfile            # Docker образ
├── start.sh              # Скрипт запуска
├── templates/            # HTML шаблоны
│   ├── base.html         # Базовый шаблон
│   ├── index.html        # Главная страница
│   ├── login.html        # Страница входа
│   ├── register.html     # Страница регистрации
│   ├── dashboard.html    # Дашборд пользователя
│   ├── project_detail.html # Детали проекта
│   ├── new_project.html  # Создание проекта
│   └── admin.html        # Админ панель
└── static/               # Статические файлы
    ├── css/              # Стили
    ├── js/               # JavaScript
    └── img/              # Изображения
```

## 🔧 Разработка

### Локальный запуск

```bash
# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
export FLASK_APP=app.py
export FLASK_ENV=development
export DATABASE_URL=postgresql://courses_user:courses_password@localhost:5432/courses_db

# Запуск
flask run
```

### Сборка Docker образа

```bash
# Сборка
docker build -t courses-webapp .

# Запуск
docker run -p 5000:5000 \
  -e POSTGRES_HOST=localhost \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=courses_db \
  -e POSTGRES_USER=courses_user \
  -e POSTGRES_PASSWORD=courses_password \
  courses-webapp
```

## 🔐 Безопасность

### Аутентификация

- Хеширование паролей с помощью Werkzeug
- Сессии пользователей через Flask-Login
- Защита маршрутов с помощью декораторов

### Авторизация

- Проверка прав доступа к проектам
- Админ панель только для администраторов
- Валидация входных данных

### Защита от атак

- CSRF защита
- Валидация файлов
- Ограничение размера загружаемых файлов

## 📊 API Endpoints

### Аутентификация
- `POST /login` - Вход в систему
- `POST /register` - Регистрация
- `GET /logout` - Выход

### Проекты
- `GET /dashboard` - Дашборд пользователя
- `GET /project/new` - Создание проекта
- `POST /project/new` - Сохранение проекта
- `GET /project/<id>` - Детали проекта
- `POST /project/<id>/upload` - Загрузка файлов
- `POST /project/<id>/process` - Запуск обработки
- `GET /project/<id>/download` - Скачивание результата

### API
- `GET /api/status/<task_id>` - Статус задачи

### Админ
- `GET /admin` - Админ панель

## 🎨 Frontend

### Компоненты

- **Навигация** - Bootstrap navbar с выпадающими меню
- **Карточки** - Отображение проектов и статистики
- **Формы** - Валидация на стороне клиента и сервера
- **Таблицы** - Адаптивные таблицы с сортировкой
- **Модальные окна** - Загрузка файлов и настройки

### Стили

- **Bootstrap 5** - Адаптивная сетка и компоненты
- **Font Awesome** - Иконки
- **Custom CSS** - Дополнительные стили

## 🗄️ База данных

### Модели

- **User** - Пользователи системы
- **Project** - Проекты Wav2Lip
- **ProcessingTask** - Задачи обработки
- **Result** - Результаты обработки

### Связи

- Пользователь → Проекты (1:N)
- Проект → Задачи (1:N)
- Проект → Результаты (1:N)

## 🚀 Развертывание

### Production

```bash
# Настройка переменных окружения
export SECRET_KEY=your-secret-key-here
export FLASK_ENV=production

# Запуск с Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
```

### Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f webapp

# Остановка
docker-compose down
```

## 🔍 Мониторинг

### Логи

```bash
# Логи веб-приложения
docker-compose logs webapp

# Логи базы данных
docker-compose logs postgres

# Все логи
docker-compose logs
```

### Здоровье системы

```bash
# Проверка веб-приложения
curl -f http://localhost:5000/

# Проверка базы данных
docker exec courses_postgres pg_isready -U courses_user -d courses_db
```

## 🚨 Устранение неполадок

### Частые проблемы

1. **Ошибка подключения к БД**
   - Проверьте статус PostgreSQL контейнера
   - Убедитесь в корректности переменных окружения

2. **Ошибка загрузки файлов**
   - Проверьте права доступа к папкам uploads/outputs
   - Убедитесь в достаточном месте на диске

3. **Ошибка аутентификации**
   - Проверьте секретный ключ
   - Очистите кэш браузера

### Восстановление

```bash
# Полная перезагрузка
docker-compose down --volumes --remove-orphans
docker-compose build --no-cache
docker-compose up -d
```

## 📚 Дополнительные ресурсы

- [Flask документация](https://flask.palletsprojects.com/)
- [SQLAlchemy документация](https://docs.sqlalchemy.org/)
- [Bootstrap документация](https://getbootstrap.com/)
- [Docker документация](https://docs.docker.com/)

## 🤝 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs webapp`
2. Убедитесь в корректности конфигурации
3. Проверьте системные требования
4. Создайте issue в репозитории проекта

---

**Courses Generator Web App** - профессиональная платформа для синхронизации видео и аудио! 🎥🎵
