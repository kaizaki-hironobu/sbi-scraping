import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import warnings
import pandas as pd
import csv
import time


warnings.simplefilter("ignore")

# User-Agentヘッダーを設定
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# float_data.csvからデータを読み込み
float_dict = {}

try:
    with open("float_data.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            float_dict[row["銘柄コード"]] = int(row["浮動株数"])
except FileNotFoundError:
    print("警告: float_data.csvが見つかりません。浮動株数取得.pyを先に実行してください。")
    float_dict = {}


data_length = 26  # 半年分（約26週間）



def convert_to_num(text):
    num = re.sub(",","",text)
    num = re.sub(r"\+[0-9]+|-[0-9]+","",num)
    return int(num)




def get_data(ticker_data,data_length=data_length):

    ticker_code = ticker_data["code"]
    ticker_kind = ticker_data["kind"]

    # リクエスト間隔を設ける（サーバー負荷軽減）
    time.sleep(0.5)

    res = requests.get("https://irbank.net/"+ticker_code+"/zandaka", headers=HEADERS)
    #print("https://irbank.net/"+ticker_code+"/zandaka")
    soup = BeautifulSoup(res.text, 'html.parser')

    rows = soup.select("#tbc > tbody > tr")
    datas = []
    for row in rows:
        inner_text = row.get_text()
        if inner_text.find("株株株")!= -1:
            continue
        if row.select_one("td.lf"):
            date = row.select_one("td.lf").get_text()
            stocks = row.select("td.rt")
            #買い銭
            mtb = stocks[0].get_text()
            #売り残+貸付残
            mts = stocks[3].get_text()
            #信用売り
            selling = stocks[1].get_text()
            

            mtb = convert_to_num(mtb)/100000
            mts = convert_to_num(mts)/100000
            selling = convert_to_num(selling)/100000


            datas.append({"date":date,"mtb":mtb,"mts":mts,"selling":selling})
    #print(datas)

    # 銘柄名を取得（取得できない場合はコードを使用）
    title_element = soup.select_one("#chb > h1 > a")
    if title_element:
        title = title_element.get_text()
        title = re.sub(" | 株式情報|"+ticker_code,"",title)
    else:
        # 銘柄名が取得できない場合はコードをそのまま使用
        title = ticker_code

    datas.reverse()
    if len(datas)>data_length:
        datas = datas[-data_length:]
    else:
        data_length = len(datas)
    if len(datas) == 0:
        return False


    buy_ratio=0
    sell_ratio=0
    selling_ratio=0
    if ticker_code in float_dict:
        if float_dict[ticker_code]!=0:
            buy_ratio=datas[-1]["mtb"]*100000/float_dict[ticker_code]*100
            sell_ratio=datas[-1]["mts"]*100000/float_dict[ticker_code]*100
            selling_ratio=datas[-1]["selling"]*100000/float_dict[ticker_code]*100




    mtbs = []

    for data in datas:
        mtbs.append(data["mtb"])

    x = np.array(range(1,len(datas)+1))
    y = np.array(mtbs)
    a,b=np.polyfit(x,y,1)

    buy_gradiation = a
    buy_approximation = b + a*data_length
    #buy_comparation =  datas[-1]["mtb"] - buy_approximation
    buy_comparation = buy_ratio - buy_approximation

    mtss = []

    for data in datas:
        mtss.append(data["mts"])

    x = np.array(range(1,len(datas)+1))
    y = np.array(mtss)

    a,b=np.polyfit(x,y,1)

    sell_gradiation = a
    sell_approximation = b + a*data_length
    #sell_comparation =  datas[-1]["mts"] - sell_approximation
    sell_comparation = sell_ratio - sell_approximation


    sellings = []

    for data in datas:
        sellings.append(data["selling"])

    x = np.array(range(1,len(datas)+1))
    y = np.array(sellings)

    a,b=np.polyfit(x,y,1)

    selling_gradiation = a
    selling_approximation = b + a*data_length
    #selling_comparation =  datas[-1]["selling"] - selling_approximation
    selling_comparation = selling_ratio - selling_approximation




    # 2つ目のリクエスト前にも待機
    time.sleep(0.5)

    res = requests.get("https://irbank.net/"+ticker_code, headers=HEADERS)

    soup = BeautifulSoup(res.text, 'html.parser')

    try:

        market_value = soup.select_one("#container > main > div.csb.cc1 > div > div > section:nth-child(1) > div:nth-child(5) > div:nth-child(2) > dl:nth-child(2) > dd:nth-child(2) > span.text").get_text()

        PBR = soup.select_one("#container > main > div.csb.cc1 > div > div > section:nth-child(1) > div:nth-child(5) > div:nth-child(2) > dl:nth-child(2) > dd:nth-child(8) > span.text").get_text()
        PER_plus = soup.select_one("#container > main > div.csb.cc1 > div > div > section:nth-child(1) > div:nth-child(5) > div:nth-child(2) > dl:nth-child(2) > dd:nth-child(6) > span.text").get_text()
        PER_minus = soup.select_one("#container > main > div.csb.cc1 > div > div > section:nth-child(1) > div:nth-child(5) > div:nth-child(2) > dl:nth-child(2) > dd:nth-child(4) > span.text").get_text()

        ROE_plus = soup.select_one("#container > main > div.csb.cc1 > div > div > section:nth-child(1) > div:nth-child(5) > div:nth-child(2) > dl:nth-child(3) > dd:nth-child(4) > span.text").get_text()
        ROE_minus = soup.select_one("#container > main > div.csb.cc1 > div > div > section:nth-child(1) > div:nth-child(5) > div:nth-child(2) > dl:nth-child(3) > dd:nth-child(2) > span.text").get_text()
        



        ROA_plus = soup.select_one("#container > main > div.csb.cc1 > div > div > section:nth-child(1) > div:nth-child(5) > div:nth-child(2) > dl:nth-child(3) > dd:nth-child(8) > span.text").get_text()
        ROA_minus = soup.select_one("#container > main > div.csb.cc1 > div > div > section:nth-child(1) > div:nth-child(5) > div:nth-child(2) > dl:nth-child(3) > dd:nth-child(6) > span.text").get_text()


    except:
        market_value = "-"
        PBR = "-"
        PER_plus = "-"
        PER_minus = "-"
        ROE_plus = "-"
        ROE_minus = "-"
        ROA_plus = "-"
        ROA_minus = "-"
    


    return {"銘柄名":title,"銘柄コード":ticker_code,"商品区分":ticker_kind,"勾配(買)":buy_gradiation,"勾配(売)":sell_gradiation,"近似値(買)":buy_approximation,"近似値(売)":sell_approximation,"直近比率(買)":buy_ratio,"直近比率(売)":sell_ratio,"差(買)":buy_comparation,"差(売)":sell_comparation,
            "勾配(信用売り)":selling_gradiation,"近似値(信用売り)":selling_approximation,"差(信用売り)":selling_comparation,"直近比率(信用売り)":selling_ratio,
            "PBR":PBR,"PER(予)":PER_plus,"PER(赤字)":PER_minus,"ROE(予)":ROE_plus,"ROE(赤字)":ROE_minus,"ROA(予)":ROA_plus,"ROA(赤字)":ROA_minus,"時価総額":market_value}


