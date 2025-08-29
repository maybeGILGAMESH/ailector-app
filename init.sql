-- Инициализация базы данных для courses_generator
-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Создание таблицы для пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Создание таблицы для проектов
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    video_path VARCHAR(500),
    text_content TEXT,
    generated_audio_path VARCHAR(500),
    output_path VARCHAR(500),
    status VARCHAR(50) DEFAULT 'pending',
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы для задач обработки
CREATE TABLE IF NOT EXISTS processing_tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    task_type VARCHAR(100) NOT NULL,
    parameters JSONB,
    status VARCHAR(50) DEFAULT 'queued',
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы для результатов
CREATE TABLE IF NOT EXISTS results (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    task_id INTEGER REFERENCES processing_tasks(id) ON DELETE CASCADE,
    file_path VARCHAR(500),
    file_size BIGINT,
    duration_seconds INTEGER,
    quality_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы для настроек
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для производительности
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON processing_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON processing_tasks(status);
CREATE INDEX IF NOT EXISTS idx_results_project_id ON results(project_id);

-- Вставка базовых настроек
INSERT INTO settings (key, value, description) VALUES
('default_fps', '25', 'Частота кадров по умолчанию'),
('default_img_size', '96', 'Размер изображения по умолчанию'),
('max_batch_size', '4', 'Максимальный размер батча'),
('temp_dir', '/tmp/wav2lip', 'Директория для временных файлов'),
('output_dir', '/output', 'Директория для результатов'),
('gpu_enabled', 'true', 'Включить GPU ускорение'),
('face_detection_model', '2dfan4', 'Модель детекции лиц'),
('audio_sample_rate', '16000', 'Частота дискретизации аудио')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description,
    updated_at = CURRENT_TIMESTAMP;

-- Создание представления для статистики
CREATE OR REPLACE VIEW project_stats AS
SELECT 
    p.id,
    p.name,
    p.status,
    u.username as user_name,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'failed' THEN 1 END) as failed_tasks,
    AVG(t.progress) as avg_progress,
    p.created_at,
    p.updated_at
FROM projects p
LEFT JOIN users u ON p.user_id = u.id
LEFT JOIN processing_tasks t ON p.id = t.project_id
GROUP BY p.id, p.name, p.status, u.username, p.created_at, p.updated_at;

-- Создание функции для обновления времени
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Создание триггеров для автоматического обновления времени
CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_settings_updated_at 
    BEFORE UPDATE ON settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Создание пользователя для приложения (если нужно)
-- CREATE USER app_user WITH PASSWORD 'app_password';
-- GRANT CONNECT ON DATABASE courses_db TO app_user;
-- GRANT USAGE ON SCHEMA public TO app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
