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
    
    def save_card_info(self, card_data, company_data=None, email_data=None, sender_email=None):
        """儲存名片資訊到Google Sheets
        
        Args:
            card_data: 名片資訊
            company_data: 公司分析資料
            email_data: 開發信內容
            sender_email: 寄件者郵件
        """
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
                    '電話', '手機', 'Email', '地址', '公司簡介', '公司類型',
                    '開發信主旨', '開發信內容', '寄件者郵件', '寄信時間'
                ]
                sheet.append_row(headers)
            elif len(headers) < 15:
                # 如果標題列不完整，更新標題列
                missing_headers = [
                    '開發信主旨', '開發信內容', '寄件者郵件', '寄信時間'
                ]
                for i, header in enumerate(missing_headers, start=len(headers)):
                    if i >= len(headers):
                        sheet.update_cell(1, i+1, header)
            
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
            
            # 如果有開發信資料，加入開發信主旨與內容
            if email_data:
                row_data.extend([
                    email_data.get('subject', ''),
                    email_data.get('content', '')
                ])
            else:
                row_data.extend(['', ''])
                
            # 加入寄件者郵件與寄信時間
            row_data.append(sender_email or '')
            
            # 如果有寄信，加入寄信時間，否則留空
            if email_data and sender_email:
                row_data.append(now)  # 使用當前時間作為寄信時間
            else:
                row_data.append('')
            
            # 新增資料列
            sheet.append_row(row_data)
            logger.info(f"成功將名片資訊儲存至Google Sheets: {card_data.get('company_name', '')}")
            
            return True
        
        except Exception as e:
            logger.error(f"儲存名片資訊至Google Sheets失敗: {str(e)}")
            return False
    
    def update_email_info(self, email, subject, content, sender_email):
        """更新已存在的記錄，添加開發信資訊
        
        Args:
            email: 收件人郵件，用於查找記錄
            subject: 開發信主旨
            content: 開發信內容
            sender_email: 寄件者郵件
        """
        if not self.client or not self.sheet_id:
            logger.error("Google Sheets客戶端未初始化或未設定Sheet ID")
            return False
        
        try:
            # 開啟工作表
            sheet = self.client.open_by_key(self.sheet_id).sheet1
            
            # 取得所有資料
            data = sheet.get_all_records()
            
            # 查找匹配的記錄
            row_index = None
            for i, row in enumerate(data, start=2):  # 從第2行開始，因為第1行是標題
                if row.get('Email') == email:
                    row_index = i
                    break
            
            if row_index:
                # 更新開發信資訊
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 獲取標題列以確定列索引
                headers = sheet.row_values(1)
                
                # 更新開發信主旨
                subject_col = headers.index('開發信主旨') + 1 if '開發信主旨' in headers else None
                if subject_col:
                    sheet.update_cell(row_index, subject_col, subject)
                
                # 更新開發信內容
                content_col = headers.index('開發信內容') + 1 if '開發信內容' in headers else None
                if content_col:
                    sheet.update_cell(row_index, content_col, content)
                
                # 更新寄件者郵件
                sender_col = headers.index('寄件者郵件') + 1 if '寄件者郵件' in headers else None
                if sender_col:
                    sheet.update_cell(row_index, sender_col, sender_email)
                
                # 更新寄信時間
                time_col = headers.index('寄信時間') + 1 if '寄信時間' in headers else None
                if time_col:
                    sheet.update_cell(row_index, time_col, now)
                
                logger.info(f"成功更新 {email} 的開發信資訊")
                return True
            else:
                logger.warning(f"未找到匹配的記錄: {email}")
                return False
        
        except Exception as e:
            logger.error(f"更新開發信資訊失敗: {str(e)}")
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