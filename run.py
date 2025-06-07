"""
名片OCR與客戶開發信系統 - 主程式入口點
"""
import os
import logging
from app import create_app

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 創建應用程式
app = create_app()

if __name__ == '__main__':
    # 取得環境變數或使用預設值
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True') == 'True'
    
    logger.info(f"啟動應用程式於 {host}:{port}, 除錯模式: {debug}")
    app.run(host=host, port=port, debug=debug) 