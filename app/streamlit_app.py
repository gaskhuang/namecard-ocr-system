"""
名片OCR與客戶開發信系統 - Streamlit介面
"""
import os
import requests
import streamlit as st
from PIL import Image
import io
import json
import logging
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 設定頁面
st.set_page_config(
    page_title="名片OCR與客戶開發信系統",
    page_icon="📇",
    layout="wide"
)

# API端點
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5001')

def main():
    """主要應用程式"""
    st.title("名片OCR與客戶開發信系統")
    st.subheader("上傳名片圖片，自動產生客戶開發信")
    
    # 初始化session state
    if 'step' not in st.session_state:
        st.session_state.step = 1
    
    if 'card_data' not in st.session_state:
        st.session_state.card_data = {}
    
    if 'company_data' not in st.session_state:
        st.session_state.company_data = {}
    
    if 'email_data' not in st.session_state:
        st.session_state.email_data = {}
    
    # 步驟1: 上傳名片
    if st.session_state.step == 1:
        step1_upload_card()
    
    # 步驟2: 確認名片資訊
    elif st.session_state.step == 2:
        step2_confirm_card_info()
    
    # 步驟3: 輸入自己公司資訊
    elif st.session_state.step == 3:
        step3_input_my_company()
    
    # 步驟4: 預覽並發送開發信
    elif st.session_state.step == 4:
        step4_preview_and_send()

def step1_upload_card():
    """步驟1: 上傳名片圖片"""
    st.header("步驟1: 上傳名片圖片", divider=True)
    
    uploaded_file = st.file_uploader("選擇名片圖片", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # 顯示圖片預覽
        image = Image.open(uploaded_file)
        st.image(image, caption="名片預覽", width=400)
        
        if st.button("上傳並辨識"):
            with st.spinner("正在上傳並辨識名片..."):
                try:
                    # 上傳圖片
                    # 重新讀取文件內容，確保文件指針在開頭
                    uploaded_file.seek(0)
                    
                    # 創建一個帶有正確文件名的文件對象
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), f"image/{uploaded_file.type.split('/')[1]}")}
                    
                    # 顯示調試信息
                    st.write(f"正在上傳文件: {uploaded_file.name}, 類型: {uploaded_file.type}")
                    
                    # 發送請求
                    response = requests.post(f"{API_BASE_URL}/upload", files=files)
                    
                    # 顯示響應狀態
                    st.write(f"上傳響應狀態碼: {response.status_code}")
                    
                    # 如果有錯誤信息，顯示它
                    if response.status_code != 200:
                        st.error(f"上傳失敗: {response.text}")
                        return
                    
                    response.raise_for_status()
                    upload_data = response.json()
                    
                    # 處理OCR
                    ocr_response = requests.post(
                        f"{API_BASE_URL}/api/ocr",
                        json={"image_path": upload_data.get("path")}
                    )
                    ocr_response.raise_for_status()
                    ocr_data = ocr_response.json()
                    
                    if ocr_data.get("status") == "success":
                        st.session_state.card_data = ocr_data.get("data", {})
                        st.session_state.step = 2
                        st.rerun()
                    else:
                        st.error(f"OCR處理失敗: {ocr_data.get('error', '未知錯誤')}")
                
                except Exception as e:
                    st.error(f"處理錯誤: {str(e)}")
                    # 顯示詳細的錯誤信息
                    import traceback
                    st.code(traceback.format_exc())

def step2_confirm_card_info():
    """步驟2: 確認名片資訊"""
    st.header("步驟2: 確認名片資訊", divider=True)
    
    # 返回按鈕
    if st.button("返回上一步"):
        st.session_state.step = 1
        st.rerun()
    
    # 顯示並允許編輯名片資訊
    with st.form("card_info_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input(
                "公司名稱", 
                value=st.session_state.card_data.get("company_name", "")
            )
            person_name = st.text_input(
                "聯絡人姓名", 
                value=st.session_state.card_data.get("person_name", "")
            )
            phone = st.text_input(
                "電話", 
                value=st.session_state.card_data.get("phone", "")
            )
            email = st.text_input(
                "Email", 
                value=st.session_state.card_data.get("email", "")
            )
        
        with col2:
            tax_id = st.text_input(
                "統一編號", 
                value=st.session_state.card_data.get("tax_id", "")
            )
            title = st.text_input(
                "職稱", 
                value=st.session_state.card_data.get("title", "")
            )
            mobile = st.text_input(
                "手機", 
                value=st.session_state.card_data.get("mobile", "")
            )
            address = st.text_input(
                "地址", 
                value=st.session_state.card_data.get("address", "")
            )
        
        submit_button = st.form_submit_button("確認並分析公司資訊")
        
        if submit_button:
            if not company_name:
                st.error("請輸入公司名稱")
            else:
                with st.spinner("正在分析公司資訊..."):
                    try:
                        # 更新session state中的名片資訊
                        st.session_state.card_data = {
                            "company_name": company_name,
                            "tax_id": tax_id,
                            "person_name": person_name,
                            "title": title,
                            "phone": phone,
                            "mobile": mobile,
                            "email": email,
                            "address": address
                        }
                        
                        # 分析公司資訊
                        analyze_response = requests.post(
                            f"{API_BASE_URL}/api/analyze",
                            json={
                                "company_name": company_name,
                                "tax_id": tax_id,
                                "address": address
                            }
                        )
                        analyze_response.raise_for_status()
                        analyze_data = analyze_response.json()
                        
                        if analyze_data.get("status") == "success":
                            st.session_state.company_data = analyze_data.get("data", {})
                            st.session_state.step = 3
                            st.rerun()
                        else:
                            st.error(f"分析失敗: {analyze_data.get('error', '未知錯誤')}")
                    
                    except Exception as e:
                        st.error(f"處理錯誤: {str(e)}")

def step3_input_my_company():
    """步驟3: 輸入自己公司資訊"""
    st.header("步驟3: 輸入自己公司資訊", divider=True)
    
    # 返回按鈕
    if st.button("返回上一步"):
        st.session_state.step = 2
        st.rerun()
    
    # 顯示目標公司分析結果
    st.subheader("目標公司分析結果")
    with st.container():
        st.markdown(f"**公司名稱:** {st.session_state.card_data.get('company_name', '')}")
        st.markdown(f"**公司簡介:** {st.session_state.company_data.get('company_profile', '')}")
        st.markdown(f"**公司類型:** {st.session_state.company_data.get('company_type', '')}")
        st.markdown(f"**產業:** {st.session_state.company_data.get('industry', '')}")
    
    st.divider()
    
    # 輸入自己公司資訊
    with st.form("my_company_form"):
        my_company_name = st.text_input("您的公司名稱")
        my_name = st.text_input("您的姓名")
        my_title = st.text_input("您的職稱")
        my_contact = st.text_input("您的聯絡方式")
        my_company_intro = st.text_area(
            "您的公司簡介", 
            placeholder="請簡述您的公司業務、產品或服務特色，以便生成更精準的開發信",
            height=150
        )
        
        submit_button = st.form_submit_button("產生開發信")
        
        if submit_button:
            if not my_company_name or not my_company_intro:
                st.error("請填寫公司名稱和公司簡介")
            else:
                with st.spinner("正在產生客戶開發信..."):
                    try:
                        # 產生開發信
                        generate_response = requests.post(
                            f"{API_BASE_URL}/api/generate-email",
                            json={
                                "target_company": {
                                    "name": st.session_state.card_data.get("company_name", ""),
                                    "profile": st.session_state.company_data.get("company_profile", ""),
                                    "type": st.session_state.company_data.get("company_type", ""),
                                    "industry": st.session_state.company_data.get("industry", ""),
                                    "contact_person": st.session_state.card_data.get("person_name", ""),
                                    "title": st.session_state.card_data.get("title", "")
                                },
                                "my_company": {
                                    "name": my_company_name,
                                    "profile": my_company_intro,
                                    "contact_person": my_name,
                                    "title": my_title,
                                    "contact": my_contact
                                }
                            }
                        )
                        generate_response.raise_for_status()
                        generate_data = generate_response.json()
                        
                        if generate_data.get("status") == "success":
                            st.session_state.email_data = generate_data.get("data", {})
                            st.session_state.my_company_data = {
                                "name": my_company_name,
                                "contact_person": my_name,
                                "title": my_title,
                                "contact": my_contact
                            }
                            st.session_state.step = 4
                            st.rerun()
                        else:
                            st.error(f"產生開發信失敗: {generate_data.get('error', '未知錯誤')}")
                    
                    except Exception as e:
                        st.error(f"處理錯誤: {str(e)}")

def step4_preview_and_send():
    """步驟4: 預覽並發送開發信"""
    st.header("步驟4: 預覽並發送開發信", divider=True)
    
    # 返回按鈕
    if st.button("返回上一步"):
        st.session_state.step = 3
        st.rerun()
    
    # 顯示郵件內容
    subject = st.text_input("郵件主旨", value=st.session_state.email_data.get("subject", ""))
    content = st.text_area("郵件內容", value=st.session_state.email_data.get("content", ""), height=300)
    recipient_email = st.text_input("收件人 Email", value=st.session_state.card_data.get("email", ""))
    
    # 初始化發送狀態
    if 'email_sent' not in st.session_state:
        st.session_state.email_sent = False
    
    if 'show_confirm' not in st.session_state:
        st.session_state.show_confirm = False
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("編輯郵件"):
            st.session_state.email_data["subject"] = subject
            st.session_state.email_data["content"] = content
            st.success("已更新郵件內容")
    
    with col2:
        # 只有在尚未發送郵件時顯示發送按鈕
        if not st.session_state.email_sent:
            if st.button("發送郵件"):
                if not recipient_email:
                    st.error("請輸入收件人 Email")
                else:
                    # 顯示確認對話框
                    st.session_state.show_confirm = True
    
    # 如果需要顯示確認對話框
    if st.session_state.show_confirm and not st.session_state.email_sent:
        with st.container():
            st.warning("確認發送郵件？")
            st.write(f"收件人: {recipient_email}")
            st.write(f"主旨: {subject}")
            
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                if st.button("確認發送", key="final_confirm"):
                    with st.spinner("正在發送郵件..."):
                        try:
                            # 發送郵件
                            send_response = requests.post(
                                f"{API_BASE_URL}/api/send-email",
                                json={
                                    "email": recipient_email,
                                    "subject": subject,
                                    "content": content
                                }
                            )
                            send_response.raise_for_status()
                            send_data = send_response.json()
                            
                            if send_data.get("status") == "success":
                                st.session_state.email_sent = True
                                st.session_state.show_confirm = False
                                st.success("📧 郵件已成功發送！")
                                st.balloons()
                            else:
                                st.error(f"發送失敗: {send_data.get('error', '未知錯誤')}")
                                st.session_state.show_confirm = False
                        
                        except Exception as e:
                            st.error(f"處理錯誤: {str(e)}")
                            st.session_state.show_confirm = False
            
            with confirm_col2:
                if st.button("取消", key="cancel_send"):
                    st.session_state.show_confirm = False
                    st.info("已取消發送")
    
    # 如果郵件已發送成功，顯示成功信息和重置按鈕
    if st.session_state.email_sent:
        st.success("📧 郵件已成功發送！")
        st.info("收件人: " + recipient_email)
        st.info("主旨: " + subject)
        
        if st.button("開始新的流程", key="new_flow"):
            st.session_state.step = 1
            st.session_state.card_data = {}
            st.session_state.company_data = {}
            st.session_state.email_data = {}
            st.session_state.email_sent = False
            st.session_state.show_confirm = False
            st.rerun()

if __name__ == "__main__":
    main() 