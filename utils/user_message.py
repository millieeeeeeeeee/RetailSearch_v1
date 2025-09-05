"""歡迎語、使用介紹"""

def hello():
    message = (
        "🎉歡迎使用【零售查詢系統】\n\n"
        "這裡能幫你快速掌握營運狀況、庫存與銷售：\n"
        "• 商品資料\n"
        "• 訂單明細\n"
        "• 會員資料"
    )
    return message


def help():
    message = (
        "ℹ️ 操作指南\n"
        "請輸入以下資訊即可得到相關資料\n\n"
        "1.會員電話或會員姓名：會員資料\n"
        "2.訂單編號：訂單明細及物流狀態\n"
        "3.商品名稱：商品編號\n"
        "4.商品編號：商品資料及庫存數量\n"   
    )
    return message

def no_data():
    message = (
        "⚠️ 查無資料，請重新輸入!"
        )

    return message
