"""
名片OCR與客戶開發信系統 - 公司資訊分析模組
"""
import os
import logging
import requests
import json
from googleapiclient.discovery import build
import google.generativeai as genai
from app.config import GOOGLE_SEARCH_API_KEY, GOOGLE_CUSTOM_SEARCH_ENGINE_ID, GEMINI_API_KEY, GEMINI_MODEL

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompanyAnalyzer:
    """公司資訊分析類別"""
    
    def __init__(self):
        """初始化公司資訊分析器"""
        # 從配置中讀取API金鑰
        self.google_api_key = GOOGLE_SEARCH_API_KEY
        self.google_cse_id = GOOGLE_CUSTOM_SEARCH_ENGINE_ID
        self.gemini_api_key = GEMINI_API_KEY
        self.gemini_model_name = GEMINI_MODEL
        
        self.google_search_client = None
        self.gemini_client = None
        
        if not self.google_api_key or not self.google_cse_id:
            logger.warning("未設定Google Search API金鑰或搜尋引擎ID，搜尋功能可能無法正常運作")
        else:
            try:
                self.google_search_client = build(
                    "customsearch", "v1", developerKey=self.google_api_key
                )
                logger.info("Google Custom Search API客戶端初始化成功")
            except Exception as e:
                logger.error(f"初始化Google Custom Search API客戶端失敗: {str(e)}")
        
        try:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel(self.gemini_model_name)
            logger.info(f"Gemini API客戶端初始化成功，使用模型: {self.gemini_model_name}")
        except Exception as e:
            logger.error(f"初始化Gemini API客戶端失敗: {str(e)}")
            self.gemini_model = None
    
    def search_company_info(self, company_name, tax_id=None, address=None):
        """搜尋公司資訊"""
        if not self.google_search_client:
            logger.error("Google Custom Search API客戶端未初始化")
            return None
        
        try:
            # 建立搜尋查詢
            query = company_name
            if tax_id:
                query += f" {tax_id}"
            if address:
                query += f" {address}"
            
            # 執行搜尋
            result = self.google_search_client.cse().list(
                q=query,
                cx=self.google_cse_id,
                num=5  # 取得前5個結果
            ).execute()
            
            # 處理搜尋結果
            search_results = []
            if 'items' in result:
                for item in result['items']:
                    search_results.append({
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', '')
                    })
            
            logger.info(f"成功搜尋公司資訊: {company_name}, 找到{len(search_results)}個結果")
            return search_results
        
        except Exception as e:
            logger.error(f"搜尋公司資訊失敗: {str(e)}")
            return None
    
    def analyze_company(self, company_name, search_results=None, tax_id=None, address=None):
        """使用Gemini分析公司資訊"""
        if not self.gemini_model:
            logger.error("Gemini API客戶端未初始化")
            return self._get_mock_company_data(company_name)
        
        try:
            # 如果沒有搜尋結果，嘗試搜尋
            if not search_results and self.google_search_client:
                search_results = self.search_company_info(company_name, tax_id, address)
            
            # 準備提示詞
            prompt = f"""請根據以下資訊，分析「{company_name}」的公司簡介、公司類型與產業。
如果資訊不足，請根據公司名稱進行合理推測。

公司名稱: {company_name}
統一編號: {tax_id or '未提供'}
地址: {address or '未提供'}

搜尋結果:
"""
            
            if search_results:
                for i, result in enumerate(search_results, 1):
                    prompt += f"""
結果 {i}:
標題: {result.get('title', '')}
連結: {result.get('link', '')}
摘要: {result.get('snippet', '')}
"""
            else:
                prompt += "未提供搜尋結果。"
            
            prompt += """
請以JSON格式回覆，格式如下:
{
  "company_profile": "公司簡介（100-200字）",
  "company_type": "公司類型（如：科技服務業、製造業、金融業等）",
  "industry": "產業分類",
  "products": ["主要產品或服務1", "主要產品或服務2", ...]
}

只需回覆JSON，不需要其他說明。
"""
            
            # 呼叫Gemini API
            response = self.gemini_model.generate_content(prompt)
            
            # 解析回應
            response_text = response.text
            
            # 嘗試從回應中提取JSON
            try:
                # 移除可能的Markdown格式
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                company_data = json.loads(response_text)
                logger.info(f"成功分析公司資訊: {company_name}")
                return company_data
            
            except json.JSONDecodeError:
                logger.error(f"解析Gemini回應JSON失敗: {response_text}")
                return self._get_mock_company_data(company_name)
        
        except Exception as e:
            logger.error(f"分析公司資訊失敗: {str(e)}")
            return self._get_mock_company_data(company_name)
    
    def generate_email(self, target_company, my_company):
        """產生客戶開發信"""
        if not self.gemini_model:
            logger.error("Gemini API客戶端未初始化")
            return self._get_mock_email()
        
        try:
            # 準備提示詞
            prompt = f"""你是 蓋斯克科技的專業資訊設備系統顧問，需要根據以下資訊生成一封專業的開發信。

客戶資訊：
- 姓名：{target_company.get('contact_person', '')}
- 公司介紹：{target_company.get('profile', '')}
- 公司產品：{', '.join(target_company.get('products', ['']))}
- 公司基本資料：公司名稱: {target_company.get('name', '')}, 產業: {target_company.get('industry', '')}, 公司類型: {target_company.get('type', '')}

蓋斯克科技基本資料：
- 寄件信箱：gask.huang@zonetech.tw
- 公司網址：www.zonetech.tw
- 寄件人：黃俊凱 Gask Huang
- 寄件職稱：資訊系統顧問

請生成一封高轉換率的開發信，遵循以下要求：
1. 信件格式與風格：
   - 語氣要像朋友間對話，避免使用敬稱（如「您」）
   - 內容要精準、專業、有說服力，不使用艱深詞彙
   - 不使用加粗或特殊符號
   - 如果提供了會面場合，在開頭提及以建立聯繫

2. 內容結構：
   第一段：提及會面場景，建立個人連結
   第二段：展示對客戶需求的理解，並提出合作價值
   第三段：根據客戶產業提供具體合作方案
   第四段：提供相關成功案例與作品集連結
   結尾段：提及前十名回信預約專案享九折優惠，並邀約進一步討論
   至少需要500字以上的信件

4. 提案重點：
   - 根據客戶產業提供2-3個具體合作方向
   - 提到相關領域的成功案例（搜尋網路上蓋斯克提供的實際案例）
   - 強調蓋斯克科技能解決的具體問題
   - 提供清晰的下一步行動方案

5. 如果資訊不足：
   - 標註出缺少哪些重要資訊
   - 建議需要補充的內容

請生成一封符合上述要求的開發信。
信件內容應包含：標題、正文、署名。

請以JSON格式回覆，格式如下:
{
  "subject": "郵件主旨",
  "content": "郵件內容"
}

只需回覆JSON，不需要其他說明。
"""
            
            # 呼叫Gemini API
            response = self.gemini_model.generate_content(prompt)
            
            # 解析回應
            response_text = response.text
            
            # 嘗試從回應中提取JSON
            try:
                # 移除可能的Markdown格式
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                email_data = json.loads(response_text)
                logger.info(f"成功產生客戶開發信: {email_data.get('subject', '')}")
                return email_data
            
            except json.JSONDecodeError:
                logger.error(f"解析Gemini回應JSON失敗: {response_text}")
                return self._get_mock_email()
        
        except Exception as e:
            logger.error(f"產生客戶開發信失敗: {str(e)}")
            return self._get_mock_email()
    
    def _get_mock_company_data(self, company_name):
        """取得模擬公司資料（當API失敗時使用）"""
        return {
            'company_profile': f'{company_name}是一家專注於提供優質產品和服務的企業，致力於滿足客戶需求並創造價值。',
            'company_type': '一般企業',
            'industry': '服務業',
            'products': ['產品服務']
        }
    
    def _get_mock_email(self):
        """取得模擬郵件（當API失敗時使用）"""
        return {
            'subject': '合作提案：提升貴公司業務效能的解決方案',
            'content': '''尊敬的客戶：

感謝您撥冗閱讀此信。我是ABC公司的業務代表，我們專注於提供優質的產品和服務，幫助企業提升效能。

經了解貴公司的業務需求，我們相信我們的解決方案能夠為貴公司帶來顯著的價值。我們的產品特點包括：
1. 高品質、高效能
2. 專業技術支援
3. 完善的售後服務

期待能有機會與您進一步討論合作可能，為貴公司提供更好的解決方案。

敬祝
事業蒸蒸日上

'''
        }

# 建立全域實例
company_analyzer = CompanyAnalyzer() 