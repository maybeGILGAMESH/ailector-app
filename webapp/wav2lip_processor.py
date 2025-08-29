#!/usr/bin/env python3
"""
Модуль для обработки видео с помощью Wav2Lip
Интеграция с веб-приложением
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Добавляем путь к Wav2Lip
sys.path.append(os.path.join(os.path.dirname(__file__), 'Wav2Lip'))

from Wav2Lip.interface import Wav2LipInterface

logger = logging.getLogger(__name__)

class Wav2LipProcessor:
    """Класс для обработки видео с помощью Wav2Lip"""
    
    def __init__(self, project_id, video_path, audio_path, output_path):
        self.project_id = project_id
        self.video_path = video_path
        self.audio_path = audio_path
        self.output_path = output_path
        
        # Создаем временную директорию для проекта
        self.temp_dir = os.path.join(os.path.dirname(__file__), 'temp', str(project_id))
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Создаем директорию для результатов
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
    def process(self):
        """Основной метод обработки"""
        try:
            logger.info(f"Начинаем обработку проекта {self.project_id}")
            
            # Создаем интерфейс Wav2Lip
            wav2lip = Wav2LipInterface(
                video_path=self.video_path,
                audio_path=self.audio_path,
                output_path=self.output_path
            )
            
            # Настраиваем параметры
            wav2lip.fps = 25
            wav2lip.img_size = 96
            wav2lip.wav2lip_batch_size = 1
            wav2lip.temp_dir = self.temp_dir
            
            # Дополнительная защита от деления на ноль
            if wav2lip.fps <= 0:
                wav2lip.fps = 25
                logger.warning(f"FPS was {wav2lip.fps}, setting to default value 25")
            
            logger.info("Запускаем генерацию Wav2Lip...")
            
            # Запускаем обработку
            wav2lip.generate()
            
            logger.info(f"Обработка завершена. Результат: {self.output_path}")
            
            return True, self.output_path
            
        except Exception as e:
            logger.error(f"Ошибка обработки Wav2Lip: {e}")
            return False, str(e)
    
    def cleanup(self):
        """Очистка временных файлов"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            logger.info(f"Временные файлы проекта {self.project_id} очищены")
        except Exception as e:
            logger.error(f"Ошибка очистки временных файлов: {e}")

def process_video_with_wav2lip(project_id, video_path, audio_path, output_path):
    """Функция для обработки видео с Wav2Lip"""
    processor = Wav2LipProcessor(project_id, video_path, audio_path, output_path)
    
    try:
        success, result = processor.process()
        return success, result
    finally:
        processor.cleanup()

if __name__ == "__main__":
    # Тестирование
    if len(sys.argv) != 5:
        print("Использование: python wav2lip_processor.py <project_id> <video_path> <audio_path> <output_path>")
        sys.exit(1)
    
    project_id = sys.argv[1]
    video_path = sys.argv[2]
    audio_path = sys.argv[3]
    output_path = sys.argv[4]
    
    success, result = process_video_with_wav2lip(project_id, video_path, audio_path, output_path)
    
    if success:
        print(f"Обработка успешна: {result}")
    else:
        print(f"Ошибка обработки: {result}")
        sys.exit(1)
