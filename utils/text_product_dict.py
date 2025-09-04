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
import config

API_KEY = config.API_KEY
API_PAGE = config.PAGE_Inventory

def get_product_summary(api_page, api_key):
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
    df_product = df[["商品編號","商品名稱"]]


    return df_product

def search_products(df, keyword):
    # 篩選 商品名稱 含有 keyword 的列
    result = df[df["商品名稱"].str.contains(keyword, na=False)]
    # 如果沒找到
    if result.empty:
        return None
    return result[["商品編號", "商品名稱"]]

def text_message_product_dict(df):
    product_boxes = []
    for i in range(len(df)):
        product_boxes.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
            {
                "type": "text",
                "text": f"{df['商品編號'].iat[i]}",
                "align": "center"
            },
            {
                "type": "separator"
            },
            {
                "type": "text",
                "text": f"{df['商品名稱'].iat[i]}",
                "align": "center"
            }
            ],
            "borderWidth": "medium"
        })

    section={
        "type": "box",
        "layout": "vertical",
        "contents": product_boxes,
        "paddingTop": "lg",
        "paddingBottom": "lg"
    }

    message={
    "type": "bubble",
    "hero": {
        "type": "box",
        "layout": "vertical",
        "contents": [
        {
            "type": "text",
            "text": "商品索引",
            "weight": "bold",
            "size": "lg",
            "align": "center"
        }
        ],
        "paddingTop": "md",
        "paddingBottom": "md",
        "backgroundColor": "#C4E1FF"
    },
    "body": section,
    "styles": {
        "header": {
        "backgroundColor": "#D2E9FF"
        }
    }
    }

    flex_json_str = json.dumps(message, ensure_ascii=False)
    flex_container = FlexContainer.from_json(flex_json_str)

    return FlexMessage(
        alt_text=f'商品索引',
        contents=flex_container
    )

def final_text_product_diCt(text):
    df=get_product_summary(API_PAGE,API_KEY)
    search_df=search_products(df,text)
    if search_df is None:
        return None
    message=text_message_product_dict(search_df)
    return message

#a=final_text_product_dixt("我")
#print(a)