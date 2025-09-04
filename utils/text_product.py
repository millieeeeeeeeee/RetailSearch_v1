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

def attach_subtable_summary(df, subtable_col):
    """
    對主表 df 的每一列，解析 subtable_col 子表格，
    並在 df 後面新增三個欄位:
      - 統計日期: 子表格最後一筆 (字串 YYYY-MM-DD 或 "None")
      - 剩餘數量: 子表格最後一筆 (int)
      - 售出總數量: 子表格全部加總 (int)
    回傳的新 df 會移除 subtable_col 欄位
    """
    results = []
    for _, row in df.iterrows():
        subtable_raw = row[subtable_col]

        if pd.isna(subtable_raw):
            results.append({"統計日期": "None", "庫存量": 0, "銷售量": 0})
            continue

        # 如果是字串要轉 dict
        if isinstance(subtable_raw, str):
            subtable_raw = ast.literal_eval(subtable_raw)

        # dict -> DataFrame
        sub_df = pd.DataFrame.from_dict(subtable_raw, orient="index")

        # 數值轉 int
        sub_df["售出數量"] = pd.to_numeric(sub_df["售出數量"], errors="coerce").fillna(0).astype(int)
        sub_df["剩餘數量"] = pd.to_numeric(sub_df["剩餘數量"], errors="coerce").fillna(0).astype(int)

        # 日期轉 datetime
        if not sub_df.empty and "統計日期" in sub_df.columns:
            sub_df["統計日期"] = pd.to_datetime(sub_df["統計日期"], errors="coerce")

        # 計算
        total_sold = int(sub_df["售出數量"].sum())
        last_row = sub_df.iloc[-1]

        # 格式化日期
        last_date = last_row["統計日期"]
        if pd.isna(last_date):
            last_date_str = "None"
        else:
            last_date_str = last_date.strftime("%Y-%m-%d")

        results.append({
            "統計日期": last_date_str,
            "庫存量": str(last_row["剩餘數量"]),
            "銷售量": str(total_sold)
        })

    # 合併到原本 df（移除 subtable_col）
    summary_df = pd.DataFrame(results)
    df_new = pd.concat([df.drop(columns=[subtable_col]).reset_index(drop=True),
                        summary_df], axis=1)
    return df_new


    # 空值或空字串都補 "查無資料"

def fill_empty(val):
    if pd.isna(val) or (isinstance(val, str) and val.strip() == ""):
        return "查無資料"
    return val


def get_product_summary(product_id, api_page, api_key):
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
    df_product = df[df["商品編號"] == product_id]

    # 若商品不存在，回傳空資料格式
    if df_product.empty:
        return None,None
    
    # 取需要的欄位
    df_summary_1 =  df_product[["商品編號","商品名稱","商品原價","剩餘庫存","商品存貨狀況","_ragicId"]]    
    df_summary_2 = df_product[["進貨廠商","聯絡電話"]]

    # 將空欄位補 "查無資料"
    df_summary_1 = df_summary_1.astype(object).apply(lambda col: col.map(fill_empty))
    df_summary_2 = df_summary_2.astype(object).apply(lambda col: col.map(fill_empty))

    #df_summary_1 = df_summary_1.applymap(fill_empty)
    #df_summary_2 = df_summary_2.applymap(fill_empty)

    return df_summary_1,df_summary_2

def text_message_product(df1,df2):
    message={
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
            {
                "type": "text",
                "text": "商品資料",
                "size": "xl",
                "weight": "bold",
                "align": "center",
                "margin": "lg"
            },
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "商品編號：",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": df1["商品編號"].iat[0],
                        "align": "end",
                        "offsetEnd": "lg",
                        "size": "sm"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "商品名稱：",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": df1["商品名稱"].iat[0],
                        "align": "end",
                        "offsetEnd": "lg",
                        "size": "sm"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "商品原價：",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": f"${(df1['商品原價'].iat[0])}",
                        "align": "end",
                        "offsetEnd": "lg",
                        "size": "sm"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "庫存量：",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": df1["剩餘庫存"].iat[0],
                        "align": "end",
                        "offsetEnd": "lg",
                        "size": "sm"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "商品存貨狀況：",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": df1["商品存貨狀況"].iat[0],
                        "align": "end",
                        "offsetEnd": "lg",
                        "size": "sm"
                    }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "進貨廠商：",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": df2["進貨廠商"].iat[0],
                        "align": "end",
                        "offsetEnd": "lg",
                        "size": "sm"
                    }
                    ],
                    "offsetTop": "sm"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "text",
                        "text": "聯絡電話：",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": df2["聯絡電話"].iat[0],
                        "align": "end",
                        "offsetEnd": "lg",
                        "size": "sm"
                    }
                    ],
                    "offsetTop": "sm"
                }
                ],
                "backgroundColor": "#F0F0F0",
                "borderWidth": "normal",
                "cornerRadius": "lg",
                "paddingStart": "lg",
                "paddingTop": "xl",
                "spacing": "sm",
                "paddingBottom": "lg"
            },
            {
                "type": "button",
                "action": {
                "type": "uri",
                "label": "查看完整商品",
                "uri": f'https://ap14.ragic.com/GoodsRecord/inventory-management2/32/{df1["_ragicId"].iat[0]}'
                },
                "style": "primary",
                "margin": "xxl",
                "height": "md"
            }
            ],
            "spacing": "sm",
            "paddingTop": "md"
        }
        }
    
    # 轉為 FlexMessage
    flex_json_str = json.dumps(message, ensure_ascii=False)
    flex_container = FlexContainer.from_json(flex_json_str)

    return FlexMessage(
        alt_text=f'{df1["商品編號"]} 商品詳細資料',
        contents=flex_container
    )

def final_text_product(text):
    df1,df2 = get_product_summary(text, API_PAGE, API_KEY)
    if df1 is None or df2 is None:
        return None
    message=text_message_product(df1,df2)
    return message

#df1,df2 = get_product_summary("P0001", API_PAGE, API_KEY)
#df1,df2 = get_product_summary("P1000",API_PAGE, API_KEY)
#message=text_message_product(df1,df2)
#pp(message)

#message_final = final_text_product("P1000")
#pp(message_final)
