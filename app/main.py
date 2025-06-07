"""
名片OCR與客戶開發信系統 - 主要路由
"""
import os
from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
import logging
from app.ocr import card_ocr
from app.analyzer import company_analyzer

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建藍圖
bp = Blueprint('main', __name__)

# 允許的檔案類型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """檢查檔案類型是否允許"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    """首頁路由"""
    return render_template('index.html')

@bp.route('/upload', methods=['POST'])
def upload_file():
    """上傳名片圖片路由"""
    logger.info("接收到上傳請求")
    
    # 檢查是否有檔案
    if 'file' not in request.files:
        logger.error("上傳失敗: 沒有檔案")
        return jsonify({'error': '沒有檔案'}), 400
    
    file = request.files['file']
    
    # 檢查檔案名稱
    if file.filename == '':
        logger.error("上傳失敗: 沒有選擇檔案")
        return jsonify({'error': '沒有選擇檔案'}), 400
    
    # 檢查檔案類型
    if not allowed_file(file.filename):
        logger.error(f"上傳失敗: 不支援的檔案類型 - {file.filename}")
        return jsonify({'error': '不支援的檔案類型'}), 400
    
    # 儲存檔案
    try:
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.instance_path, 'uploads')
        
        # 確保上傳目錄存在
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        logger.info(f"儲存檔案到: {file_path}")
        file.save(file_path)
        
        return jsonify({
            'message': '檔案上傳成功',
            'filename': filename,
            'path': file_path
        })
    except Exception as e:
        logger.error(f"檔案上傳失敗: {str(e)}")
        return jsonify({'error': f'檔案上傳失敗: {str(e)}'}), 500

@bp.route('/api/ocr', methods=['POST'])
def process_ocr():
    """處理OCR請求"""
    data = request.json
    if not data or 'image_path' not in data:
        return jsonify({'error': '缺少圖片路徑'}), 400
    
    image_path = data['image_path']
    
    try:
        # 使用OCR模組處理圖片
        logger.info(f"開始處理OCR: {image_path}")
        result = card_ocr.process_image(image_path)
        
        if not result:
            return jsonify({
                'status': 'error',
                'error': '無法辨識名片資訊'
            }), 400
        
        # 將結果轉換為前端期望的格式
        card_data = {
            'company_name': result.get('company', ''),
            'person_name': result.get('name', ''),
            'title': result.get('title', ''),
            'phone': result.get('phone', ''),
            'mobile': result.get('mobile', ''),
            'email': result.get('email', ''),
            'address': result.get('address', ''),
            'tax_id': result.get('tax_id', ''),
            'website': result.get('website', '')
        }
        
        logger.info(f"OCR處理成功: {image_path}")
        return jsonify({
            'status': 'success',
            'data': card_data
        })
        
    except Exception as e:
        logger.error(f"OCR處理失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f'OCR處理失敗: {str(e)}'
        }), 500

@bp.route('/api/analyze', methods=['POST'])
def analyze_company():
    """分析公司資訊"""
    data = request.json
    if not data or 'company_name' not in data:
        return jsonify({'error': '缺少公司名稱'}), 400
    
    company_name = data['company_name']
    tax_id = data.get('tax_id', '')
    address = data.get('address', '')
    
    try:
        # 使用公司分析模組
        logger.info(f"開始分析公司資訊: {company_name}")
        
        # 先搜尋公司資訊
        search_results = company_analyzer.search_company_info(company_name, tax_id, address)
        
        # 分析公司資訊
        result = company_analyzer.analyze_company(company_name, search_results, tax_id, address)
        
        if not result:
            return jsonify({
                'status': 'error',
                'error': '無法分析公司資訊'
            }), 400
        
        logger.info(f"公司分析成功: {company_name}")
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"公司分析失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f'公司分析失敗: {str(e)}'
        }), 500

@bp.route('/api/generate-email', methods=['POST'])
def generate_email():
    """生成開發信"""
    data = request.json
    if not data or 'target_company' not in data or 'my_company' not in data:
        return jsonify({'error': '缺少必要資訊'}), 400
    
    target_company = data['target_company']
    my_company = data['my_company']
    
    try:
        # 使用公司分析模組生成郵件
        logger.info(f"開始生成開發信: 目標公司 {target_company.get('name', '')}")
        
        result = company_analyzer.generate_email(target_company, my_company)
        
        if not result:
            return jsonify({
                'status': 'error',
                'error': '無法生成開發信'
            }), 400
        
        logger.info(f"開發信生成成功: {result.get('subject', '')}")
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"開發信生成失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f'開發信生成失敗: {str(e)}'
        }), 500

@bp.route('/api/send-email', methods=['POST'])
def send_email():
    """發送開發信"""
    data = request.json
    if not data or 'email' not in data or 'subject' not in data or 'content' not in data:
        return jsonify({'error': '缺少必要資訊'}), 400
    
    from app.mailer import gmail_sender
    
    recipient_email = data['email']
    subject = data['subject']
    content = data['content']
    
    try:
        # 實際使用Gmail API發送郵件
        logger.info(f"開始發送郵件至: {recipient_email}")
        success = gmail_sender.send_email(recipient_email, subject, content)
        
        if success:
            logger.info(f"郵件發送成功: {subject}")
            return jsonify({
                'status': 'success',
                'message': '郵件已成功寄出'
            })
        else:
            logger.error(f"郵件發送失敗: Gmail API錯誤")
            return jsonify({
                'status': 'error',
                'error': '郵件發送失敗: Gmail API錯誤'
            }), 500
            
    except Exception as e:
        logger.error(f"郵件發送失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f'郵件發送失敗: {str(e)}'
        }), 500 