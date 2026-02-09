import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

class Settings:
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    POLLINATION_API_KEY: str = os.getenv('POLLINATION_API_KEY', '')
    REPLICATE_API_TOKEN: str = os.getenv('REPLICATE_API_TOKEN', '')
    
    PRODUCTION: bool = os.getenv('PRODUCTION', 'False').lower() == 'true'
    ALLOWED_ORIGINS: list = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    
    DATA_DIR: Path = BASE_DIR / 'data'
    IMAGES_DIR: Path = DATA_DIR / 'images'
    PRESENTATIONS_DIR: Path = DATA_DIR / 'presentations'
    QUIZZES_DIR: Path = DATA_DIR / 'quizzes'
    ROADMAPS_DIR: Path = DATA_DIR / 'roadmaps'
    VIDEOS_DIR: Path = DATA_DIR / 'videos'
    REPORTS_DIR: Path = DATA_DIR / 'reports'
    
    @classmethod
    def init_directories(cls):
        for d in [cls.DATA_DIR, cls.IMAGES_DIR, cls.PRESENTATIONS_DIR, 
                  cls.QUIZZES_DIR, cls.ROADMAPS_DIR, cls.VIDEOS_DIR, cls.REPORTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.init_directories()
