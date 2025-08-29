#!/bin/bash

# Скрипт для сборки и запуска Docker контейнера с PostgreSQL
set -e

echo "🚀 Запуск сборки и запуска Docker контейнера..."

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

# Проверка версии Docker
DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
echo "✅ Docker версия: $DOCKER_VERSION"

# Проверка наличия docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose не установлен. Установите docker-compose и попробуйте снова."
    exit 1
fi

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose down --remove-orphans

# Удаление старых образов (опционально)
read -p "Удалить старые образы? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️ Удаление старых образов..."
    docker system prune -f
fi

# Сборка образа
echo "🔨 Сборка Docker образа..."
docker-compose build --no-cache

# Запуск контейнеров
echo "🚀 Запуск контейнеров..."
docker-compose up -d

# Ожидание запуска PostgreSQL
echo "⏳ Ожидание запуска PostgreSQL..."
until docker exec courses_postgres pg_isready -U courses_user -d courses_db; do
    echo "Ожидание..."
    sleep 2
done

echo "✅ PostgreSQL запущен!"

# Проверка статуса контейнеров
echo "📊 Статус контейнеров:"
docker-compose ps

# Проверка подключения к базе данных
echo "🔍 Проверка подключения к базе данных..."
docker exec courses_postgres psql -U courses_user -d courses_db -c "SELECT version();"

# Проверка созданных таблиц
echo "📋 Проверка созданных таблиц:"
docker exec courses_postgres psql -U courses_user -d courses_db -c "\dt"

# Проверка настроек
echo "⚙️ Проверка настроек:"
docker exec courses_postgres psql -U courses_user -d courses_db -c "SELECT key, value, description FROM settings;"

echo ""
echo "🎉 Контейнеры успешно запущены!"
echo ""
echo "📌 Информация о подключении:"
echo "   PostgreSQL: localhost:5432"
echo "   База данных: courses_db"
echo "   Пользователь: courses_user"
echo "   Пароль: courses_password"
echo ""
echo "🌐 pgAdmin: http://localhost:8080"
echo "   Email: admin@courses.local"
echo "   Пароль: admin123"
echo ""
echo "🔧 Полезные команды:"
echo "   Просмотр логов: docker-compose logs -f"
echo "   Остановка: docker-compose down"
echo "   Перезапуск: docker-compose restart"
echo "   Обновление: docker-compose pull && docker-compose up -d"
