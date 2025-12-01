import selenium
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import random
import re
import time
import warnings
import requests
from bs4 import BeautifulSoup
import csv
warnings.simplefilter("ignore")


def driverinit():
    options = webdriver.ChromeOptions()
    #ßoptions.add_argument("--profile-directory=default")
    #profile_path = "/Users/inouekou/Library/Application Support/Google/Chrome/"
    #options.add_argument('--user-data-dir=' + profile_path)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(ChromeDriverManager().install(),options=options)
    driver.implicitly_wait(5)
    return driver

driver = driverinit()

driver.get("https://site1.sbisec.co.jp/ETGate/?_ControlID=WPLETsiR001Control&_PageID=WPLETsiR001Idtl50&_DataStoreID=DSWPLETsiR001Control&_ActionID=DefaultAID&s_rkbn=2&s_btype=&i_stock_sec=3133&i_dom_flg=1&i_exchange_code=JPN&i_output_type=4&exchange_code=TKY&stock_sec_code_mul=3133&ref_from=1&ref_to=20&getFlg=on&wstm4130_sort_id=&wstm4130_sort_kbn=&qr_keyword=1&qr_suggest=1&qr_sort=1")

with open("ID.txt") as f:
    id = f.read()
with open("password.txt") as f:
    password = f.read()

time.sleep(1)
driver.find_element_by_css_selector("input[name='user_id']").send_keys(id)
time.sleep(2)
driver.find_element_by_css_selector("input[name='user_password']").send_keys(password)
time.sleep(2)
driver.find_element_by_css_selector("input[name='ACT_login']").click()
time.sleep(2)

driver.implicitly_wait(0.3)

def get_float_rate(ticker_code):
    driver.get("https://site1.sbisec.co.jp/ETGate/?_ControlID=WPLETsiR001Control&_PageID=WPLETsiR001Idtl50&_DataStoreID=DSWPLETsiR001Control&_ActionID=DefaultAID&s_rkbn=2&s_btype=&i_stock_sec="+ticker_code+"&i_dom_flg=1&i_exchange_code=JPN&i_output_type=4&exchange_code=TKY&stock_sec_code_mul="+ticker_code+"&ref_from=1&ref_to=20&getFlg=on&wstm4130_sort_id=&wstm4130_sort_kbn=&qr_keyword=1&qr_suggest=1&qr_sort=1")

    float_rate = driver.find_element_by_css_selector("#main > div.shikihouBox01 > table:nth-child(2) > tbody > tr > td:nth-child(1) > table:nth-child(2) > tbody > tr:nth-child(1) > td:nth-child(3)").text

    float_rate = float(re.sub("%","",float_rate))/100.0


    res = requests.get("https://finance.yahoo.co.jp/quote/"+ticker_code+".T")
    soup = BeautifulSoup(res.text, 'html.parser')

    try:
        text = soup.select_one("#referenc > div > ul > li:nth-child(2) > dl > dd > span._1fofaCjs._2aohzPlv._1DMRub9m > span > span._3rXWJKZF._11kV6f2G").get_text()
    except AttributeError:
        print("発行済み株式数が存在しない")
        return False
    all_stock_amount = re.sub(",| |(株)","",text)
    time.sleep(0.2)

    return float_rate,all_stock_amount


datas=[]
with open("stocks.txt") as f:
    text=f.read()
    tickers=text.split("\n")

#for ticker in tickers[:20]:
for ticker in tickers:
    try:
        float_rate,all_stock_amount=get_float_rate(ticker)
        float_amount=int(int(all_stock_amount)*float_rate)
        print(ticker,float_amount)
        if float_amount>=0:
            datas.append([ticker,str(int(int(all_stock_amount)*float_rate))])
    except:
        print("エラー")

print(datas)

text=""
for data in datas:
    text+=data[0]+","+data[1]+"\n"
text=text[:-1]

with open("float_data.txt","w",encoding="utf-8") as f:
    f.write(text)
print("取得が完了しました")