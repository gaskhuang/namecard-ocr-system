"""
名片OCR與客戶開發信系統 - 配置檔案
"""
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 應用程式配置
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')

# Google API 配置
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT')
GOOGLE_SEARCH_API_KEY = os.environ.get('GOOGLE_SEARCH_API_KEY', 'AIzaSyArJRJUMRH35I5MM8uwE_oEcvAgRwzDc34')
GOOGLE_CUSTOM_SEARCH_ENGINE_ID = os.environ.get('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')

# Gemini API 配置
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyAaIdVle4LB3Hq_LMmSDaF503zSmyfh2sY')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-preview-05-20')

# Gmail API 配置
GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_CLIENT_SECRET_FILE = os.environ.get('GMAIL_CLIENT_SECRET_FILE')

# 上傳檔案配置
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Google Sheets 配置
GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID')
GOOGLE_SHEET_RANGE = os.environ.get('GOOGLE_SHEET_RANGE', 'Sheet1!A:Z') 