#!/usr/bin/env python3
"""
Клиент для работы с PostgreSQL базой данных courses_generator
"""

import psycopg2
import psycopg2.extras
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Project:
    """Класс для представления проекта"""
    id: Optional[str] = None
    name: str = ""
    description: str = ""
    video_path: str = ""
    audio_path: str = ""
    output_path: str = ""
    status: str = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class ProcessingTask:
    """Класс для представления задачи обработки"""
    id: Optional[str] = None
    project_id: str = ""
    task_type: str = ""
    parameters: Dict[str, Any] = None
    status: str = "queued"
    progress: int = 0
    error_message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

@dataclass
class Result:
    """Класс для представления результата"""
    id: Optional[str] = None
    project_id: str = ""
    task_id: str = ""
    file_path: str = ""
    file_size: int = 0
    duration_seconds: int = 0
    quality_metrics: Dict[str, Any] = None
    created_at: Optional[datetime] = None

class DatabaseClient:
    """Клиент для работы с базой данных"""
    
    def __init__(self, host: str = "localhost", port: int = 5432, 
                 database: str = "courses_db", user: str = "courses_user", 
                 password: str = "courses_password"):
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.conn = None
    
    def connect(self) -> bool:
        """Подключение к базе данных"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            logger.info("Успешное подключение к базе данных")
            return True
        except psycopg2.Error as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            return False
    
    def disconnect(self):
        """Отключение от базы данных"""
        if self.conn:
            self.conn.close()
            logger.info("Отключение от базы данных")
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Dict]]:
        """Выполнение SQL запроса"""
        if not self.conn:
            logger.error("Нет подключения к базе данных")
            return None
        
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    self.conn.commit()
                    return None
        except psycopg2.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            self.conn.rollback()
            return None
    
    def create_project(self, project: Project) -> Optional[str]:
        """Создание нового проекта"""
        query = """
        INSERT INTO projects (name, description, video_path, audio_path, output_path, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (project.name, project.description, project.video_path, 
                 project.audio_path, project.output_path, project.status)
        
        result = self.execute_query(query, params)
        if result:
            project_id = result[0]['id']
            logger.info(f"Проект создан с ID: {project_id}")
            return project_id
        return None
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Получение проекта по ID"""
        query = "SELECT * FROM projects WHERE id = %s"
        result = self.execute_query(query, (project_id,))
        
        if result:
            data = result[0]
            return Project(**data)
        return None
    
    def get_all_projects(self) -> List[Project]:
        """Получение всех проектов"""
        query = "SELECT * FROM projects ORDER BY created_at DESC"
        result = self.execute_query(query)
        
        if result:
            return [Project(**data) for data in result]
        return []
    
    def update_project_status(self, project_id: str, status: str) -> bool:
        """Обновление статуса проекта"""
        query = "UPDATE projects SET status = %s WHERE id = %s"
        result = self.execute_query(query, (status, project_id))
        return result is not None
    
    def create_task(self, task: ProcessingTask) -> Optional[str]:
        """Создание новой задачи обработки"""
        query = """
        INSERT INTO processing_tasks (project_id, task_type, parameters, status, progress)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (task.project_id, task.task_type, 
                 json.dumps(task.parameters) if task.parameters else None,
                 task.status, task.progress)
        
        result = self.execute_query(query, params)
        if result:
            task_id = result[0]['id']
            logger.info(f"Задача создана с ID: {task_id}")
            return task_id
        return None
    
    def update_task_progress(self, task_id: str, progress: int, status: str = None) -> bool:
        """Обновление прогресса задачи"""
        if status:
            query = "UPDATE processing_tasks SET progress = %s, status = %s WHERE id = %s"
            params = (progress, status, task_id)
        else:
            query = "UPDATE processing_tasks SET progress = %s WHERE id = %s"
            params = (progress, task_id)
        
        result = self.execute_query(query, params)
        return result is not None
    
    def complete_task(self, task_id: str, status: str = "completed") -> bool:
        """Завершение задачи"""
        query = """
        UPDATE processing_tasks 
        SET status = %s, completed_at = CURRENT_TIMESTAMP 
        WHERE id = %s
        """
        result = self.execute_query(query, (status, task_id))
        return result is not None
    
    def create_result(self, result: Result) -> Optional[str]:
        """Создание результата"""
        query = """
        INSERT INTO results (project_id, task_id, file_path, file_size, duration_seconds, quality_metrics)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (result.project_id, result.task_id, result.file_path,
                 result.file_size, result.duration_seconds,
                 json.dumps(result.quality_metrics) if result.quality_metrics else None)
        
        result_data = self.execute_query(query, params)
        if result_data:
            result_id = result_data[0]['id']
            logger.info(f"Результат создан с ID: {result_id}")
            return result_id
        return None
    
    def get_project_stats(self, project_id: str) -> Optional[Dict]:
        """Получение статистики проекта"""
        query = "SELECT * FROM project_stats WHERE id = %s"
        result = self.execute_query(query, (project_id,))
        
        if result:
            return dict(result[0])
        return None
    
    def get_settings(self) -> Dict[str, str]:
        """Получение всех настроек"""
        query = "SELECT key, value FROM settings"
        result = self.execute_query(query)
        
        if result:
            return {row['key']: row['value'] for row in result}
        return {}
    
    def update_setting(self, key: str, value: str) -> bool:
        """Обновление настройки"""
        query = "UPDATE settings SET value = %s WHERE key = %s"
        result = self.execute_query(query, (value, key))
        return result is not None

def main():
    """Пример использования клиента"""
    # Создание клиента
    db_client = DatabaseClient()
    
    if not db_client.connect():
        logger.error("Не удалось подключиться к базе данных")
        return
    
    try:
        # Создание проекта
        project = Project(
            name="Тестовый проект",
            description="Тестовый проект для проверки работы",
            video_path="/path/to/video.mp4",
            audio_path="/path/to/audio.mp3",
            output_path="/path/to/output.mp4"
        )
        
        project_id = db_client.create_project(project)
        if project_id:
            logger.info(f"Проект создан: {project_id}")
            
            # Создание задачи
            task = ProcessingTask(
                project_id=project_id,
                task_type="wav2lip_sync",
                parameters={"fps": 25, "img_size": 96},
                status="queued"
            )
            
            task_id = db_client.create_task(task)
            if task_id:
                logger.info(f"Задача создана: {task_id}")
                
                # Обновление прогресса
                db_client.update_task_progress(task_id, 50, "processing")
                
                # Завершение задачи
                db_client.complete_task(task_id)
                
                # Создание результата
                result = Result(
                    project_id=project_id,
                    task_id=task_id,
                    file_path="/path/to/result.mp4",
                    file_size=1024000,
                    duration_seconds=30,
                    quality_metrics={"sync_accuracy": 0.95}
                )
                
                result_id = db_client.create_result(result)
                if result_id:
                    logger.info(f"Результат создан: {result_id}")
        
        # Получение всех проектов
        projects = db_client.get_all_projects()
        logger.info(f"Всего проектов: {len(projects)}")
        
        # Получение настроек
        settings = db_client.get_settings()
        logger.info(f"Настройки: {settings}")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    finally:
        db_client.disconnect()

if __name__ == "__main__":
    main()
