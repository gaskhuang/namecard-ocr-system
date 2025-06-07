"""
名片OCR與客戶開發信系統 - 主程式入口點
"""
import os
import logging
import subprocess
import sys
import time
import threading
from app import create_app

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def start_streamlit():
    """在子進程中啟動 Streamlit 應用程式"""
    streamlit_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'streamlit_app.py')
    logger.info(f"啟動 Streamlit 應用程式: {streamlit_app_path}")
    
    # 使用 subprocess 啟動 Streamlit
    try:
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", streamlit_app_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info("Streamlit 應用程式已啟動，請在瀏覽器中開啟 http://localhost:8501")
        
        # 監控 Streamlit 輸出
        def monitor_output():
            for line in streamlit_process.stdout:
                logger.info(f"Streamlit: {line.strip()}")
            for line in streamlit_process.stderr:
                logger.error(f"Streamlit 錯誤: {line.strip()}")
        
        threading.Thread(target=monitor_output, daemon=True).start()
        
        return streamlit_process
    except Exception as e:
        logger.error(f"啟動 Streamlit 失敗: {str(e)}")
        return None

# 創建應用程式
app = create_app()

if __name__ == '__main__':
    # 取得環境變數或使用預設值
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True') == 'True'
    
    # 啟動 Streamlit 應用程式
    streamlit_process = start_streamlit()
    
    # 給 Streamlit 一些時間啟動
    time.sleep(2)
    
    # 啟動 Flask 應用程式
    logger.info(f"啟動 Flask 應用程式於 {host}:{port}, 除錯模式: {debug}")
    try:
        app.run(host=host, port=port, debug=debug)
    finally:
        # 確保在 Flask 應用程式結束時也關閉 Streamlit
        if streamlit_process:
            logger.info("關閉 Streamlit 應用程式")
            streamlit_process.terminate() 