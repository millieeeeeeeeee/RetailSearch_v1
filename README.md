# RetailSearch_v1
這是一個**零售查詢系統**的LINEBot串接Ragic!資料庫，包含主程式、設定檔、工具函數、圖片以及 Docker，並部署至Google Cloud實現24小時運作。

```bash
├── main.py              # 主程式入口
├── config.py            # 設定檔（環境變數、密碼等）
├── utils/               # 工具函數模組
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
|收到M+4碼數字|查會員ID|會員資料|  
|收到數字|查會員電話|會員資料| 
|收到P+4碼數字|查商品編號|商品資料| 
|收到O+4碼數字|查訂單編號|訂單明細| 
|收到其他文字|查商品名稱|商品索引| 
|收到其他文字且查不到資料|查商品編號|查無資料 + 使用指南| 

## 工具函數模組
> user_message.py

1. 歡迎訊息
2. 使用指南
3. 查無資料
> text_product.py

1. 商品編號查詢商品資料
> text_product_dict.py

1. 商品名稱查詢商品索引
> text_order.py

1. 訂單編號查詢訂單明細
> text_member.py

1. 會員ID查詢會員資料
2. 會員電話查詢會員資料
> setting_text.py

1. 收到文字訊息的回覆邏輯處理

## 設定檔
> config.py
1. Linebot
   - access_token
   - secret
3. Ragic!
   - API_key
   - PAGE_Orders(URL)
   - PAGE_Inventory(URL)
   - PAGE_Customers(URL)


## 專案技術
- line-bot-sdk
- flask
- gunicorn
- google-cloud

## 第三方服務
- LINE BOT
- Ragic!
