"""
名片OCR與客戶開發信系統 - 應用程式初始化
"""
import os
from flask import Flask
from dotenv import load_dotenv
from flask_cors import CORS

# 載入環境變數
load_dotenv()

def create_app(test_config=None):
    """創建並設定Flask應用程式"""
    # 創建Flask應用程式
    app = Flask(__name__, instance_relative_config=True)
    
    # 啟用CORS，允許所有來源的跨域請求
    CORS(app)
    
    # 設定預設配置
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DEBUG=os.environ.get('DEBUG', 'True') == 'True',
    )

    if test_config is None:
        # 如果不是測試環境，則從環境變數載入配置
        app.config.from_pyfile('config.py', silent=True)
    else:
        # 如果是測試環境，則載入測試配置
        app.config.from_mapping(test_config)

    # 確保instance資料夾存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 註冊藍圖
    from app import main
    app.register_blueprint(main.bp)

    # 註冊路由
    @app.route('/health')
    def health_check():
        """健康檢查路由"""
        return {'status': 'ok'}

    return app 