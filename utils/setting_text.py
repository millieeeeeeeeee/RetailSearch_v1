import re

from utils.text_member import *
from utils.text_product import *
from utils.text_product_dict import *
from utils.text_order import *
from utils.user_message import *

def choose_text_function(text):
    search_member_text = re.sub(r"[^0-9\u4e00-\u9fffA-Za-z]", "", text)
    reply = None
    # 會員ID/電話號碼查詢
    if re.fullmatch(r"M\d{4}", text) or search_member_text.isdigit():
        reply = final_text_member(search_member_text)
    # 商品編號查詢
    elif re.fullmatch(r"P\d{4}", text):
        reply = final_text_product(text)
    # 訂單編號查詢   
    elif re.fullmatch(r"O\d{4}", text):
        reply = final_text_order(text)
    
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


