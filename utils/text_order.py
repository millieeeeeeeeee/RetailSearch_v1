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
API_PAGE = config.PAGE_Orders

def fill_empty(val):
    if pd.isna(val) or (isinstance(val, str) and val.strip() == ""):
        return "查無資料"
    return val

def attach_subtable_summary_v2(df, subtable_col):
    """
    對主表 df 的每一列，解析 subtable_col 子表格，
    並在 df 後面新增:
      - 商品編號: 最後一筆 (字串) 或 "查無資料"
      - 商品數量: 最後一筆 (int) 或 "查無資料"
    回傳的新 df 會移除 subtable_col 欄位
    """
    results = []
    for _, row in df.iterrows():
        subtable_raw = row[subtable_col]

        # 無資料
        if pd.isna(subtable_raw) or subtable_raw in ["", None, {}, []]:
            results.append({"商品編號": "查無資料", "商品數量": "查無資料"})
            continue

        # 嘗試轉換成 dict
        if isinstance(subtable_raw, str):
            try:
                subtable_raw = ast.literal_eval(subtable_raw)
            except Exception:
                results.append({"商品編號": "查無資料", "商品數量": "查無資料"})
                continue

        # dict -> DataFrame
        try:
            sub_df = pd.DataFrame.from_dict(subtable_raw, orient="index")
        except Exception:
            results.append({"商品編號": "查無資料", "商品數量": "查無資料"})
            continue

        # 確保欄位存在
        if "商品編號" not in sub_df.columns or "商品數量" not in sub_df.columns or sub_df.empty:
            results.append({"商品編號": "查無資料", "商品數量": "查無資料"})
            continue

        # 數值轉 int
        sub_df["商品數量"] = pd.to_numeric(sub_df["商品數量"], errors="coerce").fillna(0).astype(int)

        # 取最後一筆資料
        last_row = sub_df.iloc[-1]
        results.append({
            "商品編號": str(last_row.get("商品編號", "查無資料")),
            "商品數量": int(last_row.get("商品數量", 0)) if pd.notna(last_row.get("商品數量")) else "查無資料"
        })

    # 合併到原本 df（移除 subtable_col）
    summary_df = pd.DataFrame(results)
    df_new = pd.concat([df.drop(columns=[subtable_col]).reset_index(drop=True),
                        summary_df], axis=1)
    return df_new

def attach_subtable_summary(df, subtable_col):
    """
    對主表 df 的每一列，解析 subtable_col 子表格，
    將每筆子表資料展開成獨立列，
    回傳新的 DataFrame，包含：
      - 原本 df 的欄位
      - 商品編號
      - 商品名稱
      - 商品數量
    若子表無資料，仍保留一列，商品欄位為 "查無資料"
    """
    all_rows = []

    for _, row in df.iterrows():
        subtable_raw = row[subtable_col]

        # 無資料
        if pd.isna(subtable_raw) or subtable_raw in ["", None, {}, []]:
            new_row = row.to_dict()
            new_row.update({"商品編號": "查無資料", "商品名稱": "查無資料", "商品數量": "查無資料"})
            all_rows.append(new_row)
            continue

        # 嘗試轉成 dict/list
        if isinstance(subtable_raw, str):
            try:
                subtable_raw = ast.literal_eval(subtable_raw)
            except Exception:
                new_row = row.to_dict()
                new_row.update({"商品編號": "查無資料", "商品名稱": "查無資料", "商品數量": "查無資料"})
                all_rows.append(new_row)
                continue

        # dict -> DataFrame
        try:
            sub_df = pd.DataFrame.from_dict(subtable_raw, orient="index")
        except Exception:
            new_row = row.to_dict()
            new_row.update({"商品編號": "查無資料", "商品名稱": "查無資料", "商品數量": "查無資料"})
            all_rows.append(new_row)
            continue

        # 確保欄位存在
        for col in ["商品編號", "商品名稱", "商品數量"]:
            if col not in sub_df.columns:
                sub_df[col] = "查無資料"

        # 數值轉 int
        sub_df["商品數量"] = pd.to_numeric(sub_df["商品數量"], errors="coerce").fillna(0).astype(int)

        # 展開每筆子表資料
        for _, sub_row in sub_df.iterrows():
            new_row = row.to_dict()
            new_row.update({
                "商品編號": str(sub_row["商品編號"]),
                "商品名稱": str(sub_row["商品名稱"]),
                "商品數量": int(sub_row["商品數量"])
            })
            all_rows.append(new_row)

    new_df = pd.DataFrame(all_rows)
    new_df = new_df.drop(columns=[subtable_col], errors="ignore")
    return new_df

def get_order_summary(order_id, api_page, api_key):
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
    df_product = df[df["訂單編號"] == order_id]

    # 若商品不存在，回傳空資料格式
    if df_product.empty:
        return None,None
    
    # 取需要的欄位
    df_summary_1 = df_product[["訂單編號","會員ID","總金額","訂單來源","付款類型","訂單日期","訂單狀態","配送方式","_ragicId"]]    
    #df_summary_2 = df_product[["_subtable_1000163"]]
    df_need = df_product[["_subtable_1000163"]]

    # 格式化日期
    last_date = df_summary_1["訂單日期"].iloc[0]
    if pd.isna(last_date):
        last_date_str = "None"
    else:
        last_date_str = pd.to_datetime(last_date).strftime("%Y-%m-%d")
    df_summary_1.loc[:, "訂單日期"] = last_date_str

    # 整理子表格
    df_summary_2 = attach_subtable_summary(df_need, "_subtable_1000163")

    # 將空欄位補 "查無資料"
    df_summary_1 = df_summary_1.astype(object).apply(lambda col: col.map(fill_empty))
    df_summary_2 = df_summary_2.astype(object).apply(lambda col: col.map(fill_empty))

    #df_summary_1 = df_summary_1.applymap(fill_empty)
    #df_summary_2 = df_summary_2.applymap(fill_empty)

    return df_summary_1,df_summary_2

def text_message_order(df1,df2):
    product_boxes = []
    for i in range(len(df2)):
        product_boxes.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [{
                        "type": "text",
                        "text": f"【{df2['商品編號'].iat[i]}】",
                        "size": "xs",
                        "flex": 2
                    },
                    {
                        "type": "text",
                        "text": f"{df2['商品名稱'].iat[i]}",
                        "size": "xs",
                        "flex": 3
                    },
                    {
                        "type": "text",
                        "text": f'x{df2["商品數量"].iat[0]}',
                        "size": "xs",
                        "align": "start",
                        "flex": 1
                    }
                ,
                {
                    "type": "filler"
                }
            ],
            "paddingStart": "md",
            "paddingEnd": "xl"
        })

    # 原本訂購項目區塊
    product_section = {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "訂購項目：",
                "size": "sm"
            }
        ] + product_boxes,  # 把迴圈生成的商品 box 加進去
        "offsetTop": "sm"
    }

    message = {
    "type": "bubble",
    "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
        {
            "type": "text",
            "text": "訂單明細",
            "size": "xl",
            "weight": "bold",
            "align": "center"
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
                    "text": "訂單編號：",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": df1["訂單編號"].iat[0],
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
                    "text": "會員ID：",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": df1["會員ID"].iat[0],
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
                    "text": "總金額(含運)：",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": df1["總金額"].iat[0],
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
                    "text": "訂購/付款方式：",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": f'{df1["訂單來源"].iat[0]}/{df1["付款類型"].iat[0]}',
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
                    "text": "配送方式：",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": f'{df1["配送方式"].iat[0]}',
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
                    "text": "訂購日期：",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": df1["訂單日期"].iat[0],
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
                    "text": "訂單狀態：",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": df1["訂單狀態"].iat[0],
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
            product_section,
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "text",
                    "text": "訂購備註：",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": "無",
                    "size": "xs",
                    "offsetStart": "lg"
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
            "label": "查看完整訂單",
            "uri": f'https://ap14.ragic.com/GoodsRecord/inventory-management2/36/{df1["_ragicId"].iat[0]}'
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
    
    # 將原本 JSON 中的單一商品區塊替換成 product_section
    #message["body"]["contents"][1]["contents"][9] = product_section
    # 轉為 FlexMessage
    flex_json_str = json.dumps(message, ensure_ascii=False)
    flex_container = FlexContainer.from_json(flex_json_str)

    return FlexMessage(
        alt_text=f'{df1["訂單編號"].iat[0]} 訂單詳細資料',
        contents=flex_container
    )

def final_text_order(text):
    df1,df2 = get_order_summary(text, API_PAGE, API_KEY)
    if df1 is None or df2 is None:
        return None
    message=text_message_order(df1,df2)
    return message



#df_summary_1,df_summary_2 = get_order_summary("O0002", API_PAGE, API_KEY)
#print(df_summary_1)
#print(df_summary_2)

#a=final_text_order("O0002")
#print(a)

