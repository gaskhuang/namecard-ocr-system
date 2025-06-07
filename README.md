# 名片OCR與客戶開發信系統

這是一個自動化名片資訊處理與客戶開發信產生系統。用戶上傳名片圖片後，系統自動辨識名片內容，將資訊存入 Google Sheet，並自動搜尋公司相關資料，分析公司簡介與類型，最後根據雙方公司資訊自動產生並寄送客戶開發信。

## 主要功能

- 圖片上傳與 Google OCR 文字辨識
- 名片資訊自動分欄存入 Google Sheet
- 公司資訊自動 Google 搜尋
- Claude API 分析公司簡介與類型
- 用戶輸入自己公司介紹
- Claude API 產生專屬客戶開發信（含標題與內容）
- Gmail API 寄送開發信，寄出前 Yes/No 確認

## 安裝與設定

### 環境需求
- Python 3.9+
- Google Cloud 帳號（需啟用 Vision API, Custom Search API, Sheets API）
- Anthropic API 金鑰（Claude）
- Gmail API 存取權限

### 安裝步驟
1. 複製專案
   ```bash
   git clone [repository-url]
   cd namecard-system
   ```

2. 建立虛擬環境
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或 venv\Scripts\activate  # Windows
   ```

3. 安裝依賴套件
   ```bash
   pip install -r requirements.txt
   ```

4. 設定環境變數
   ```bash
   cp .env.example .env
   # 編輯 .env 檔案，填入必要的 API 金鑰
   ```

## 使用方式

1. 啟動應用程式
   ```bash
   python run.py
   ```

2. 在瀏覽器中開啟 http://localhost:8501

3. 依照介面指示上傳名片圖片，確認辨識結果，輸入公司介紹，預覽並發送開發信

## 專案結構

```
namecard-system/
├── app/                    # 應用程式主要程式碼
│   ├── __init__.py
│   ├── main.py             # Flask 應用程式
│   ├── streamlit_app.py    # Streamlit 介面
│   ├── config.py           # 設定檔
│   ├── static/             # 靜態資源
│   └── templates/          # HTML 模板
├── tests/                  # 測試程式碼
├── .env.example            # 環境變數範例
├── requirements.txt        # 依賴套件清單
└── run.py                  # 主程式進入點
```

## 授權

本專案採用 MIT 授權條款 - 詳見 LICENSE 檔案
