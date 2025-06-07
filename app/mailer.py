"""
名片OCR與客戶開發信系統 - Gmail API郵件發送模組
"""
import os
import logging
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gmail API 範圍
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailSender:
    """Gmail API郵件發送類別"""
    
    def __init__(self):
        """初始化Gmail發送器"""
        self.client = None
        self.credentials = None
        
        # 嘗試從.env.gmail文件讀取配置
        gmail_env_file = '.env.gmail'
        if os.path.exists(gmail_env_file):
            try:
                with open(gmail_env_file, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
                logger.info("從.env.gmail讀取Gmail配置成功")
            except Exception as e:
                logger.error(f"讀取.env.gmail文件失敗: {str(e)}")
        
        self.user_email = os.environ.get('GMAIL_USER')
        
        # 檢查是否有設定Gmail用戶
        if not self.user_email:
            logger.warning("未設定GMAIL_USER環境變數，郵件功能可能無法正常運作")
        
        # 檢查是否有設定Gmail API憑證檔案
        client_secret_file = os.environ.get('GMAIL_CLIENT_SECRET_FILE')
        if not client_secret_file:
            logger.warning("未設定GMAIL_CLIENT_SECRET_FILE環境變數，郵件功能可能無法正常運作")
            return
        
        # 檢查憑證檔案是否存在
        if not os.path.exists(client_secret_file):
            logger.error(f"Gmail API憑證檔案不存在: {client_secret_file}")
            return
        
        # 初始化Gmail客戶端
        try:
            # 嘗試載入已存在的憑證
            token_file = 'token.pickle'
            if os.path.exists(token_file):
                with open(token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
            
            # 如果沒有有效憑證，則進行OAuth流程
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
                    self.credentials = flow.run_local_server(port=0)
                
                # 儲存憑證以供下次使用
                with open(token_file, 'wb') as token:
                    pickle.dump(self.credentials, token)
            
            # 建立Gmail API客戶端
            self.client = build('gmail', 'v1', credentials=self.credentials)
            logger.info("Gmail API客戶端初始化成功")
        
        except Exception as e:
            logger.error(f"初始化Gmail API客戶端失敗: {str(e)}")
            self.client = None
    
    def send_email(self, to, subject, body):
        """發送郵件"""
        if not self.client or not self.user_email:
            logger.error("Gmail API客戶端未初始化或未設定用戶郵件")
            return False
        
        try:
            # 建立郵件
            message = MIMEMultipart()
            message['to'] = to
            message['from'] = self.user_email
            message['subject'] = subject
            
            # 添加內容
            message.attach(MIMEText(body, 'plain'))
            
            # 編碼郵件
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # 發送郵件
            self.client.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"成功發送郵件至: {to}")
            return True
        
        except Exception as e:
            logger.error(f"發送郵件失敗: {str(e)}")
            return False
    
    def send_html_email(self, to, subject, html_body):
        """發送HTML格式郵件"""
        if not self.client or not self.user_email:
            logger.error("Gmail API客戶端未初始化或未設定用戶郵件")
            return False
        
        try:
            # 建立郵件
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['from'] = self.user_email
            message['subject'] = subject
            
            # 添加HTML內容
            message.attach(MIMEText(html_body, 'html'))
            
            # 編碼郵件
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # 發送郵件
            self.client.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"成功發送HTML郵件至: {to}")
            return True
        
        except Exception as e:
            logger.error(f"發送HTML郵件失敗: {str(e)}")
            return False

# 建立全域實例
gmail_sender = GmailSender() 