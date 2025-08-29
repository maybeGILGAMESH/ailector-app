#!/bin/bash

# Скрипт настройки PostgreSQL контейнера
set -e

echo "Настройка PostgreSQL контейнера..."

# Ожидание запуска PostgreSQL
until pg_isready -U $POSTGRES_USER -d $POSTGRES_DB; do
    echo "Ожидание запуска PostgreSQL..."
    sleep 2
done

echo "PostgreSQL запущен!"

# Создание дополнительных пользователей и прав (опционально)
if [ "$CREATE_APP_USER" = "true" ]; then
    echo "Создание пользователя приложения..."
    psql -U $POSTGRES_USER -d $POSTGRES_DB <<-EOSQL
        CREATE USER app_user WITH PASSWORD 'app_password';
        GRANT CONNECT ON DATABASE $POSTGRES_DB TO app_user;
        GRANT USAGE ON SCHEMA public TO app_user;
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
EOSQL
    echo "Пользователь приложения создан!"
fi

# Проверка подключения
echo "Проверка подключения к базе данных..."
psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT version();"

# Проверка созданных таблиц
echo "Проверка созданных таблиц..."
psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"

# Проверка настроек
echo "Проверка настроек..."
psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT key, value, description FROM settings;"

echo "Настройка PostgreSQL завершена!"
