"""
名片OCR與客戶開發信系統 - OCR模組
"""
import os
import io
import logging
import re
from PIL import Image
import google.generativeai as genai
from google.oauth2 import service_account
from google.cloud import vision

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BusinessCardOCR:
    """名片OCR類別"""
    
    def __init__(self):
        """初始化OCR處理器"""
        self.vision_client = None
        self.gemini_model = None
        
        # 檢查是否有設定Google Cloud認證
        credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        gemini_api_key = os.environ.get('GEMINI_API_KEY', 'AIzaSyAaIdVle4LB3Hq_LMmSDaF503zSmyfh2sY')
        
        # 初始化Vision API客戶端（作為備用）
        if credentials_path and os.path.exists(credentials_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.vision_client = vision.ImageAnnotatorClient(credentials=credentials)
                logger.info("Google Vision API客戶端初始化成功")
            except Exception as e:
                logger.error(f"初始化Google Vision API客戶端失敗: {str(e)}")
        else:
            logger.warning("未設定Google Cloud認證或檔案不存在，Vision API功能可能無法正常運作")
        
        # 初始化Gemini API客戶端
        try:
            genai.configure(api_key=gemini_api_key)
            # 使用Gemini 2.5 Flash模型
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
            logger.info("Gemini API客戶端初始化成功")
        except Exception as e:
            logger.error(f"初始化Gemini API客戶端失敗: {str(e)}")
            logger.warning("Gemini API初始化失敗，OCR功能可能無法正常運作")
    
    def process_image(self, image_path):
        """處理圖片並辨識文字"""
        # 優先使用Gemini 2.5 Flash進行OCR
        if self.gemini_model:
            try:
                return self._process_with_gemini(image_path)
            except Exception as e:
                logger.error(f"使用Gemini處理圖片失敗: {str(e)}")
                logger.info("嘗試使用備用Vision API...")
        
        # 備用：使用Google Vision API
        if self.vision_client:
            try:
                return self._process_with_vision_api(image_path)
            except Exception as e:
                logger.error(f"使用Vision API處理圖片失敗: {str(e)}")
        
        logger.error("所有OCR處理方法均失敗")
        return None
    
    def _process_with_gemini(self, image_path):
        """使用Gemini 2.5 Flash處理圖片OCR"""
        logger.info(f"使用Gemini 2.5 Flash處理圖片: {image_path}")
        
        try:
            # 讀取圖片
            image = Image.open(image_path)
            
            # 準備提示詞
            prompt = """
            這是一張名片圖片。請執行OCR提取所有文字，並將資訊結構化為以下JSON格式：
            {
              "name": "人名",
              "title": "職稱",
              "company": "公司名稱",
              "phone": "電話號碼",
              "mobile": "手機號碼",
              "email": "電子郵件",
              "address": "地址",
              "website": "網站",
              "tax_id": "統一編號（如果有）",
              "raw_text": "完整提取的文字"
            }
            
            請注意：
            1. 名片通常包含人名、職稱、公司名稱、聯絡資訊等
            2. 人名通常位於名片上方，字體較大
            3. 統一編號通常是8位數字，可能標示為「統一編號」或「統編」
            4. 請盡可能準確提取所有資訊
            5. 如果某些欄位資訊不存在，請將對應值設為空字串
            6. 只需回覆JSON格式，不需要其他說明
            """
            
            # 呼叫Gemini API
            response = self.gemini_model.generate_content([prompt, image])
            response_text = response.text
            
            # 嘗試從回應中提取JSON
            try:
                # 移除可能的Markdown格式
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                import json
                card_info = json.loads(response_text)
                logger.info(f"成功使用Gemini處理圖片文字: {image_path}")
                return card_info
            
            except json.JSONDecodeError as e:
                logger.error(f"解析Gemini回應JSON失敗: {response_text}")
                logger.error(f"JSON錯誤: {str(e)}")
                # 嘗試使用備用方法解析文字
                return self._parse_text_fallback(response_text)
        
        except Exception as e:
            logger.error(f"Gemini處理圖片失敗: {str(e)}")
            raise
    
    def _process_with_vision_api(self, image_path):
        """使用Google Vision API處理圖片OCR（備用方法）"""
        if not self.vision_client:
            logger.error("Google Vision API客戶端未初始化")
            return None
        
        try:
            # 讀取圖片
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            # 建立圖片物件
            image = vision.Image(content=content)
            
            # 執行OCR
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations
            
            if not texts:
                logger.warning(f"未在圖片中找到文字: {image_path}")
                return None
            
            # 取得完整文字
            full_text = texts[0].description
            logger.info(f"成功使用Vision API辨識圖片文字: {image_path}")
            
            # 解析名片資訊
            card_info = self._parse_business_card(full_text)
            
            # 檢查是否有錯誤
            if response.error.message:
                logger.error(f"Google Vision API錯誤: {response.error.message}")
            
            return card_info
        
        except Exception as e:
            logger.error(f"Vision API處理圖片失敗: {str(e)}")
            return None
    
    def _parse_text_fallback(self, text):
        """當JSON解析失敗時的備用解析方法"""
        # 初始化結果
        result = {
            'name': '',
            'title': '',
            'company': '',
            'phone': '',
            'mobile': '',
            'email': '',
            'address': '',
            'website': '',
            'tax_id': '',
            'raw_text': text
        }
        
        # 嘗試從文字中提取資訊
        try:
            # 提取電子郵件
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            if email_match:
                result['email'] = email_match.group(0)
            
            # 提取網站
            website_match = re.search(r'(https?://)?([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}(/[-a-zA-Z0-9%_.~#?&=]*)?', text)
            if website_match:
                result['website'] = website_match.group(0)
            
            # 提取電話號碼
            phone_match = re.search(r'[\(\)（）]?\d{2,4}[\(\)（）]?[-\s]?\d{3,4}[-\s]?\d{3,4}', text)
            if phone_match:
                result['phone'] = phone_match.group(0)
            
            # 提取統一編號
            tax_id_match = re.search(r'\d{8}', text)
            if tax_id_match:
                result['tax_id'] = tax_id_match.group(0)
            
            # 嘗試提取其他資訊
            lines = text.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                
                # 跳過空行
                if not line:
                    continue
                
                # 提取公司名稱
                if ('公司' in line or '企業' in line or '集團' in line) and not result['company'] and len(line) < 30:
                    result['company'] = line
                
                # 提取姓名（通常是較短的行，且在名片的前幾行）
                if i < 3 and not result['name'] and len(line) < 10:
                    if not any(x in line.lower() for x in ['電話', 'tel', 'www', 'http', '@', '股份', '有限']):
                        result['name'] = line
                
                # 提取職稱
                if ('經理' in line or '主任' in line or '總監' in line or '工程師' in line) and not result['title'] and len(line) < 20:
                    result['title'] = line
                
                # 提取地址
                if ('市' in line or '縣' in line or '路' in line or '街' in line) and not result['address'] and len(line) > 10:
                    result['address'] = line
        
        except Exception as e:
            logger.error(f"備用解析方法失敗: {str(e)}")
        
        return result
    
    def _parse_business_card(self, text):
        """解析名片文字，提取關鍵資訊"""
        # 初始化結果
        result = {
            'name': '',
            'title': '',
            'company': '',
            'phone': '',
            'mobile': '',
            'email': '',
            'address': '',
            'website': '',
            'tax_id': '',
            'raw_text': text
        }
        
        # 分行處理
        lines = text.split('\n')
        
        # 解析每一行
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 跳過空行
            if not line:
                continue
            
            # 提取電子郵件
            if '@' in line and not result['email']:
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', line)
                if email_match:
                    result['email'] = email_match.group(0)
                    continue
            
            # 提取網站
            if ('http://' in line or 'https://' in line or 'www.' in line) and not result['website']:
                website_match = re.search(r'(https?://)?([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}(/[-a-zA-Z0-9%_.~#?&=]*)?', line)
                if website_match:
                    result['website'] = website_match.group(0)
                    continue
            
            # 提取電話號碼
            if ('電話' in line or 'Tel' in line.lower() or 'T:' in line) and not result['phone']:
                phone_match = re.search(r'[\(\)（）]?\d{2,4}[\(\)（）]?[-\s]?\d{3,4}[-\s]?\d{3,4}', line)
                if phone_match:
                    result['phone'] = phone_match.group(0)
                    continue
            
            # 提取手機號碼
            if ('手機' in line or 'Mobile' in line.lower() or 'M:' in line) and not result['mobile']:
                mobile_match = re.search(r'[\(\)（）]?\d{2,4}[\(\)（）]?[-\s]?\d{3,4}[-\s]?\d{3,4}', line)
                if mobile_match:
                    result['mobile'] = mobile_match.group(0)
                    continue
            
            # 提取統一編號
            if ('統一編號' in line or '統編' in line) and not result['tax_id']:
                tax_id_match = re.search(r'\d{8}', line)
                if tax_id_match:
                    result['tax_id'] = tax_id_match.group(0)
                    continue
            
            # 提取地址（通常較長且包含地址相關詞）
            if ('市' in line or '縣' in line or '路' in line or '街' in line or '區' in line) and not result['address']:
                # 檢查是否為地址（通常地址較長）
                if len(line) > 10:
                    result['address'] = line
                    continue
            
            # 提取職稱（通常在名字後面或公司前面）
            if ('經理' in line or '主任' in line or '總監' in line or '工程師' in line or 
                'Manager' in line or 'Director' in line or 'Engineer' in line) and not result['title']:
                # 如果這行包含職稱關鍵字，但不是完整的地址或其他已識別資訊
                if not result['title'] and len(line) < 20:
                    # 嘗試提取職稱部分
                    title_match = re.search(r'(?:^|\s)([^0-9]+(?:經理|主任|總監|工程師|Manager|Director|Engineer)[^0-9]*)(?:\s|$)', line)
                    if title_match:
                        result['title'] = title_match.group(1).strip()
                    else:
                        result['title'] = line
                    continue
            
            # 提取公司名稱（通常包含「公司」、「企業」、「集團」等字眼）
            if ('公司' in line or '企業' in line or '集團' in line or 'Co.' in line or 'Ltd' in line or 'Inc' in line) and not result['company']:
                # 如果這行可能是公司名稱
                if len(line) < 30:  # 避免取到太長的行
                    result['company'] = line
                    continue
            
            # 提取姓名（通常是較短的行，且在名片的前幾行）
            if i < 3 and not result['name'] and len(line) < 10:
                # 檢查是否為可能的姓名（不含常見的非姓名元素）
                if not any(x in line.lower() for x in ['電話', 'tel', 'www', 'http', '@', '股份', '有限']):
                    result['name'] = line
                    continue
        
        # 如果沒有找到公司名稱，嘗試從前幾行提取
        if not result['company']:
            for i, line in enumerate(lines):
                if i < 5 and '公司' in line and len(line) < 30:
                    result['company'] = line
                    break
        
        # 如果沒有找到姓名，使用第一行非空文字
        if not result['name']:
            for line in lines:
                if line.strip() and len(line) < 10:
                    result['name'] = line
                    break
        
        # 返回結果
        return result

# 建立全域實例
card_ocr = BusinessCardOCR() 