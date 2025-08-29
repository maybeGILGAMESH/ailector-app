#!/bin/bash

# Скрипт запуска веб-приложения
set -e

echo "🚀 Запуск Courses Generator Web App..."

# Ожидание запуска PostgreSQL
echo "⏳ Ожидание запуска PostgreSQL..."
until pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB; do
    echo "Ожидание PostgreSQL..."
    sleep 2
done

echo "✅ PostgreSQL доступен!"

# Создание таблиц базы данных
echo "🔧 Инициализация базы данных..."
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('База данных инициализирована')
"

# Запуск приложения
echo "🌐 Запуск веб-приложения..."
if [ "$FLASK_ENV" = "development" ]; then
    python3 app.py
else
    gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
fi
