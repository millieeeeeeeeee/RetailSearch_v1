# RetailSearch_v1
這是一個**零售查詢系統**的LINEBot串接Ragic!資料庫，包含主程式、設定檔、工具函數、圖片以及 Docker，並部署至Google Cloud實現24小時運作。

```bash
├── main.py              # 主程式入口
├── config.py            # 設定檔（環境變數、密碼等）
├── utils/               # 工具函數模組
│              
├── images/              # 圖片資源
│ 
├── Dockerfile           # Docker 建置檔
├── requirements.txt     # Python 依賴套件
└── README.md            # 專案說明文件
```

## 畫面

## 功能總覽

|操作|流程|內容| 
|------------|----------|--------|
|首次加入好友|無|歡迎訊息 + 使用指南|  
|收到文字訊息|無|使用指南|  

## 工具函數模組
> user_message.py

1. 歡迎訊息
2. 使用指南
> setting_richmenu.py

1. 設定主選單(圖片、功能數量、回傳參數)

## 設定檔
> config.py
1. Linebot
   - access_token
   - secret

## 專案技術
- line-bot-sdk
- flask
- gunicorn
- google-cloud

## 第三方服務
- LINE BOT
- Ragic!
