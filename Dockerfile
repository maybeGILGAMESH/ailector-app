FROM postgres:15-alpine

# Установка дополнительных утилит
RUN apk add --no-cache \
    bash \
    curl \
    vim \
    postgresql-contrib

# Создание пользователя и базы данных
ENV POSTGRES_USER=courses_user
ENV POSTGRES_PASSWORD=courses_password
ENV POSTGRES_DB=courses_db

# Копирование скриптов инициализации
COPY ./init.sql /docker-entrypoint-initdb.d/
COPY ./setup.sh /docker-entrypoint-initdb.d/

# Установка прав на выполнение
RUN chmod +x /docker-entrypoint-initdb.d/setup.sh

# Открытие порта
EXPOSE 5432

# Установка переменных окружения для производительности
ENV POSTGRES_INITDB_ARGS="--encoding=UTF-8 --lc-collate=C --lc-ctype=C"
ENV PGDATA=/var/lib/postgresql/data/pgdata

# Создание директории для данных
RUN mkdir -p /var/lib/postgresql/data && \
    chown -R postgres:postgres /var/lib/postgresql/data

# Переключение на пользователя postgres
USER postgres

# Запуск PostgreSQL
CMD ["postgres"]
