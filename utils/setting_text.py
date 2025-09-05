import re

from utils.text_member import *
from utils.text_product import *
from utils.text_product_dict import *
from utils.text_order import *
from utils.user_message import *

def choose_text_function(text):
    # 把輸入清理掉特殊字元，只留數字/中英文
    search_member_text = re.sub(r"[^0-9\u4e00-\u9fffA-Za-z]", "", text)
    reply = None

    # 會員ID (M1234) 或電話號碼 (純數字)
    if re.fullmatch(r"M\d{4}", search_member_text) or search_member_text.isdigit():
        reply = final_text_member(search_member_text)

    # 商品編號 (P1234)
    elif re.fullmatch(r"P\d{4}", search_member_text):
        reply = final_text_product(search_member_text)

    # 訂單編號 (O1234)
    elif re.fullmatch(r"O\d{4}", search_member_text):
        reply = final_text_order(search_member_text)

    # 會員姓名 (其他情況)
    else:
        reply = final_text_member(search_member_text)

    # 商品名稱模糊查詢
    if reply is None:
        reply = final_text_product_diCt(text)

    # 如果還是找不到
    if reply is None:
        return [
            TextMessage(text=str(no_data())),
            TextMessage(text=str(help()))     
        ]
    else:
        return [reply]
