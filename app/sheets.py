"""
名片OCR與客戶開發信系統 - Google Sheets處理模組
"""
import os
import logging
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Sheets API 範圍
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class SheetsProcessor:
    """Google Sheets處理類別"""
    
    def __init__(self):
        """初始化Google Sheets處理器"""
        # 檢查是否有設定Google Cloud憑證
        credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        sheet_id = os.environ.get('GOOGLE_SHEET_ID')
        
        self.client = None
        self.sheet_id = sheet_id
        
        if not credentials_path:
            logger.warning("未設定GOOGLE_APPLICATION_CREDENTIALS環境變數，Sheets功能可能無法正常運作")
            return
        
        if not sheet_id:
            logger.warning("未設定GOOGLE_SHEET_ID環境變數，Sheets功能可能無法正常運作")
        
        # 初始化Sheets客戶端
        try:
            credentials = Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES
            )
            self.client = gspread.authorize(credentials)
            logger.info("Google Sheets API客戶端初始化成功")
        except Exception as e:
            logger.error(f"初始化Google Sheets API客戶端失敗: {str(e)}")
            self.client = None
    
    def save_card_info(self, card_data, company_data=None):
        """儲存名片資訊到Google Sheets"""
        if not self.client or not self.sheet_id:
            logger.error("Google Sheets客戶端未初始化或未設定Sheet ID")
            return False
        
        try:
            # 開啟工作表
            sheet = self.client.open_by_key(self.sheet_id).sheet1
            
            # 檢查標題列
            headers = sheet.row_values(1)
            if not headers:
                # 如果沒有標題列，新增標題列
                headers = [
                    '時間戳記', '公司名稱', '統一編號', '聯絡人', '職稱', 
                    '電話', '手機', 'Email', '地址', '公司簡介', '公司類型'
                ]
                sheet.append_row(headers)
            
            # 準備資料
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            row_data = [
                now,
                card_data.get('company_name', ''),
                card_data.get('tax_id', ''),
                card_data.get('person_name', ''),
                card_data.get('title', ''),
                card_data.get('phone', ''),
                card_data.get('mobile', ''),
                card_data.get('email', ''),
                card_data.get('address', '')
            ]
            
            # 如果有公司分析資料，加入公司簡介與類型
            if company_data:
                row_data.extend([
                    company_data.get('company_profile', ''),
                    company_data.get('company_type', '')
                ])
            else:
                row_data.extend(['', ''])
            
            # 新增資料列
            sheet.append_row(row_data)
            logger.info(f"成功將名片資訊儲存至Google Sheets: {card_data.get('company_name', '')}")
            
            return True
        
        except Exception as e:
            logger.error(f"儲存名片資訊至Google Sheets失敗: {str(e)}")
            return False
    
    def get_all_cards(self):
        """取得所有名片資訊"""
        if not self.client or not self.sheet_id:
            logger.error("Google Sheets客戶端未初始化或未設定Sheet ID")
            return []
        
        try:
            # 開啟工作表
            sheet = self.client.open_by_key(self.sheet_id).sheet1
            
            # 取得所有資料
            data = sheet.get_all_records()
            logger.info(f"成功從Google Sheets取得{len(data)}筆名片資訊")
            
            return data
        
        except Exception as e:
            logger.error(f"從Google Sheets取得名片資訊失敗: {str(e)}")
            return []

# 建立全域實例
sheets_processor = SheetsProcessor() 