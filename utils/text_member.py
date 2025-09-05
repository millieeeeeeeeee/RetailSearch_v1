import re
import ast
import json
import requests
import pandas as pd
from pprint import pprint as pp
from datetime import datetime, timedelta
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage,
    FlexMessage, FlexContainer
)

API_KEY = 'S0lBRXU1UkhIaVh2NnQzaVR3Y2NyeDczbm5VU3ptTHcrMEFydGxqN1BQQjM3UVFIU0phZ0V1RkQvTTR1dDZBdQ=='

API_PAGE = 'https://ap14.ragic.com/GoodsRecord/inventory-management2/36?PAGEID=ll4'

def fill_empty(val):
    if pd.isna(val) or (isinstance(val, str) and val.strip() == ""):
        return "查無資料"
    return val

# 統一日期格式
def change_date(df,column):
    
    last_date = df[column].iloc[0]
    if pd.isna(last_date):
        last_date_str = "None"
    else:
        last_date_str = pd.to_datetime(last_date).strftime("%Y-%m-%d")
    df.loc[:, column] = last_date_str

# 統一電話格式
def change_phone(df,column):
    phone = df[column].iloc[0]
    if pd.isna(phone):
        phone = "None"
    else:
        phone = re.sub(r"(\d{4})(\d+)", r"\1-\2", phone.replace("-", ""))
    df.loc[:, column] = phone

def get_member_summary(member_id, api_page, api_key):
    """
    下載 API 資料，整理成 DataFrame，並回傳指定商品的整理後資訊
    """
    params = {
        'api': '',
        'v': 3
    }
    response = requests.get(api_page, params=params, headers={'Authorization': 'Basic ' + api_key})
    response_dict = response.json()

    df = pd.DataFrame.from_dict(response_dict, orient="index")

    # 篩選指定商品
    df_product = df[df["會員ID"] == member_id]

    # 若商品不存在，回傳空資料格式
    if df_product.empty:
        df_tel = df[["會員電話", "會員姓名","會員ID"]].dropna().copy()
        df_tel.loc[:, "會員電話"] = df_tel["會員電話"].str.replace(r"[^0-9]", "", regex=True)
        return None,None,df_tel
    
    # 取需要的欄位
    df_summary_1 = df_product[["會員ID","會員姓名","會員生日","會員性別","會員電話","居住地址"]]   #會員姓名
    df_summary_2 = df_product[["訂單編號","訂單日期","訂單狀態"]]

    # 新增欄位「歷史訂單數」
    order_count = len(df_summary_2)
    df_summary_1["歷史訂單數"] = order_count

    # 格式化日期
    change_date(df_summary_1,"會員生日")
    change_date(df_summary_2,"訂單日期")

    # 格式化電話
    change_phone(df_summary_1,"會員電話")

    # 將空欄位補 "查無資料"
    df_summary_1 = df_summary_1.astype(object).apply(lambda col: col.map(fill_empty))
    df_summary_2 = df_summary_2.astype(object).apply(lambda col: col.map(fill_empty))

    #df_summary_1 = df_summary_1.applymap(fill_empty)
    #df_summary_2 = df_summary_2.applymap(fill_empty)


    #額外處理df_summary_3用來檢索電話、姓名
    
    return df_summary_1,df_summary_2,None

def text_message_member(df1,df2):
    # 迴圈生成每筆訂單 box
    order_boxes = []
    for i in range(len(df2)):
        order_box = {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": df2['訂單日期'].iat[i],
                    "size": "sm",
                    "color": "#111111",
                    "flex": 1
                },
                {
                    "type": "text",
                    "text": df2['訂單編號'].iat[i],
                    "size": "sm",
                    "color": "#111111",
                    "align": "end",
                    "flex": 1
                },
                {
                    "type": "text",
                    "text": df2['訂單狀態'].iat[i],
                    "size": "sm",
                    "color": "#555555",
                    "align": "end",
                    "flex": 1
                }
            ],
            "paddingStart": "lg"
        }
        order_boxes.append(order_box)

    # 主訊息
    message = {
        "type": "bubble",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "會員資料",
                    "weight": "bold",
                    "size": "lg",
                    "align": "center"
                }
            ],
            "paddingTop": "md",
            "paddingBottom": "md",
            "backgroundColor": "#D8D8EB"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        # 會員基本資料
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "會員ID：", "size": "sm", "color": "#555555", "flex": 0},
                                {"type": "text", "text": df1['會員ID'].iat[0], "size": "sm", "color": "#111111", "align": "end"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "會員姓名：", "size": "sm", "color": "#555555", "flex": 0},
                                {"type": "text", "text": df1['會員姓名'].iat[0], "size": "sm", "color": "#111111", "align": "end"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "會員電話：", "size": "sm", "color": "#555555", "flex": 0},
                                {"type": "text", "text": df1['會員電話'].iat[0], "size": "sm", "color": "#111111", "align": "end"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "會員生日：", "size": "sm", "color": "#555555", "flex": 0},
                                {"type": "text", "text": df1['會員生日'].iat[0], "size": "sm", "color": "#111111", "align": "end"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "會員性別：", "size": "sm", "color": "#555555", "flex": 0},
                                {"type": "text", "text": df1['會員性別'].iat[0], "size": "sm", "color": "#111111", "align": "end"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "會員地址：", "size": "sm", "color": "#555555", "flex": 0},
                                {"type": "text", "text": df1['居住地址'].iat[0], "size": "sm", "color": "#111111", "align": "end"}
                            ]
                        },
                        {"type": "separator", "margin": "xxl"},
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "margin": "xxl",
                            "contents": [
                                {"type": "text", "text": "歷史訂單：", "size": "sm", "color": "#555555"},
                                {"type": "text", "text": str(df1['歷史訂單數'].iat[0]), "size": "sm", "color": "#111111", "align": "end"}
                            ]
                        },
                        # 🔥 把 order_boxes 插入這裡
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": order_boxes
                        }
                    ]
                }
            ],
            "paddingTop": "lg",
            "paddingBottom": "lg"
        },
        "styles": {"footer": {"separator": True}}
    }

    flex_json_str = json.dumps(message, ensure_ascii=False)
    flex_container = FlexContainer.from_json(flex_json_str)

    return FlexMessage(
        alt_text=f'{df1["會員ID"].iat[0]} 會員詳細資料',
        contents=flex_container
    )


def final_text_member(text):
    df1, df2, df_tel = get_member_summary(text, API_PAGE, API_KEY)
    if df_tel is None:
        message = text_message_member(df1, df2)
        return message
    elif text in df_tel["會員電話"].values:
        member_id = df_tel.loc[df_tel["會員電話"] == text, "會員ID"].iloc[0]
        df1, df2, df_tel = get_member_summary(member_id, API_PAGE, API_KEY)
        message = text_message_member(df1, df2)
        return message
    elif text in df_tel["會員姓名"].values:
        member_id = df_tel.loc[df_tel["會員姓名"] == text, "會員ID"].iloc[0]
        df1, df2, df_tel = get_member_summary(member_id, API_PAGE, API_KEY)
        message = text_message_member(df1, df2)
        return message
    else:
        return None



#df_summary_1,df_summary_2,df_tel = get_member_summary("顏濤甯", API_PAGE, API_KEY)
#print(df_summary_1)
#print(df_summary_2)
#print(df_tel)

#member_id = df_tel.loc[df_tel["會員電話"] == "謝又姝", "會員ID"].iloc[0]
#print(member_id)

#a=final_text_member("M1036")
#a=final_text_member("0998-654287")
#a=final_text_member("顏濤甯")
#print(a)
