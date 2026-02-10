import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import warnings
import tkinter
import scraping
import sys
import tkinter as tk
import threading
import pandas as pd
import tqdm
import math
warnings.simplefilter("ignore")

def round_up(value, decimals=2):
    """小数点第2位で切り上げ"""
    multiplier = 10 ** decimals
    return math.ceil(value * multiplier) / multiplier



def search():
    pass

def stocks_to_list():
    stockdata = []
    with open("stocks.txt",encoding="utf-8") as f:
        all_codes = f.read().splitlines()
    with open("kinds.txt",encoding  ="utf-8") as f:
        all_kinds = f.read().splitlines()
    for i in range(len(all_codes)):
        stockdata.append({"code":all_codes[i],"kind":all_kinds[i]})
    return stockdata
all_stocks = stocks_to_list()

def get_calculated_data():
    # ファイル名のバリデーション
    if not filenamebox.get().strip():
        print("エラー: ファイル名を入力してください")
        return

    print("データ取得中...")
    datas = []
    for stock in tqdm.tqdm(all_stocks):
        data = scraping.get_data(stock,26)  # 半年分（約26週間）
        datas.append(data)
    print("取得完了")
    print(datas)

    display_datas = []

    for data in datas:
        if data == False:
            continue
        if var1.get():
            if var12.get():
                if data["勾配(売)"]>float(textBox1.get()):
                    continue
            else:
                if data["勾配(売)"]<float(textBox1.get()):
                    continue
        if var2.get():
            if var14.get():
                if data["直近比率(売)"]>float(textBox2.get()):
                    continue
            else:
                if data["直近比率(売)"]<float(textBox2.get()):
                    continue
        if var3.get():
            if var16.get():
                if data["近似値(売)"]>float(textBox3.get()):
                    continue
            else:
                if data["近似値(売)"]<float(textBox3.get()):
                    continue
        if var4.get():
            if var18.get():
                if data["差(売)"]>float(textBox4.get()):
                    continue
            else:
                if data["差(売)"]<float(textBox4.get()):
                    continue
        if var5.get():
            if var20.get():
                if data["勾配(買)"]>float(textBox5.get()):
                    continue
            else:
                if data["勾配(買)"]<float(textBox5.get()):
                    continue
        if var6.get():
            if var22.get():
                if data["直近比率(買)"]>float(textBox6.get()):
                    continue
            else:
                if data["直近比率(買)"]<float(textBox6.get()):
                    continue
        if var7.get():
            if var22.get():
                if data["近似値(買)"]>float(textBox7.get()):
                    continue
            else:
                if data["近似値(買)"]<float(textBox7.get()):
                    continue
        if var8.get():
            if var24.get():
                if data["差(買)"]>float(textBox8.get()):
                    continue
            else:
                if data["差(買)"]<float(textBox8.get()):
                    continue
        
        ok_flag = False
        if prime_var.get():
            if data["商品区分"].find("プライム")!=-1:
                ok_flag = True
        if growth_var.get():
            if data["商品区分"].find("グロース")!=-1:
                ok_flag = True
        if standard_var.get():
            if data["商品区分"].find("スタンダード")!=-1:
                ok_flag = True
        if ok_flag == False:
            continue


        display_datas.append([data["銘柄コード"],data["銘柄名"],round_up(data["勾配(売)"]),round_up(data["近似値(売)"]),round_up(data["直近比率(売)"]),round_up(data["差(売)"]),round_up(data["勾配(買)"]),round_up(data["近似値(買)"]),round_up(data["直近比率(買)"]),round_up(data["差(買)"])])
    print("取得が完了しました")
    if ascend_var.get() or descend_var.get():
        if sort_sell_gradient_var.get():
            display_datas = sorted(display_datas,key=lambda x:x[2])
        if sort_sell_approximation_var.get():
            display_datas = sorted(display_datas,key=lambda x:x[3])
        if sort_sell_ratio_var.get():
            display_datas = sorted(display_datas,key=lambda x:x[4])
        if sort_sell_comparation_var.get():
            display_datas = sorted(display_datas,key=lambda x:x[5])
        if sort_buy_gradient_var.get():
            display_datas = sorted(display_datas,key=lambda x:x[6])
        if sort_buy_approximation_var.get():
            display_datas = sorted(display_datas,key=lambda x:x[7])
        if sort_buy_ratio_var.get():
            display_datas = sorted(display_datas,key=lambda x:x[8])
        if sort_buy_comparation_var.get():
            display_datas = sorted(display_datas,key=lambda x:x[9])
    
    if descend_var.get():
        display_datas.reverse()

    pd.DataFrame(display_datas,columns=["銘柄コード","銘柄名","勾配(売)","近似値(売)","直近比率(売)","差(売)","勾配(買)","近似値(買)","直近比率(買)","差(買)"]).to_csv(filenamebox.get()+".csv",index=False,encoding="cp932")

def on_scraping():
    threading.Thread(target=get_calculated_data).start()


root = tkinter.Tk()                     
root.title("株価取得.py")     
root.geometry("400x600")


extract_button = tkinter.Button(root, text="取得", width=20,command=on_scraping)
extract_button.place(x=120, y=550)





starty = 20
duration = 30


var1 = tkinter.BooleanVar()
chk1 = tkinter.Checkbutton(root, text='勾配（売）', variable=var1)
chk1.place(x=30,y=starty)

var2 = tkinter.BooleanVar()
chk2 = tkinter.Checkbutton(root, text='直近比率（売）', variable=var2)
chk2.place(x=30,y=starty+duration)

var3 = tkinter.BooleanVar()
chk3 = tkinter.Checkbutton(root, text='近似値（売）', variable=var3)
chk3.place(x=30,y=starty+duration*2)

var4 = tkinter.BooleanVar()
chk4 = tkinter.Checkbutton(root, text='差（売）', variable=var4)
chk4.place(x=30,y=starty+duration*3)

var5 = tkinter.BooleanVar()
chk5 = tkinter.Checkbutton(root, text='勾配（買）', variable=var5)
chk5.place(x=30,y=starty+duration*4)

var6 = tkinter.BooleanVar()
chk6 = tkinter.Checkbutton(root, text='直近比率（買）', variable=var6)
chk6.place(x=30,y=starty+duration*5)

var7 = tkinter.BooleanVar()
chk7 = tkinter.Checkbutton(root, text='近似値（買）', variable=var7)
chk7.place(x=30,y=starty+duration*6)

var8 = tkinter.BooleanVar()
chk8 = tkinter.Checkbutton(root, text='差（買）', variable=var8)
chk8.place(x=30,y=starty+duration*7)

textBox1 = tkinter.Entry(width=10)
textBox1.place(x=135, y=starty)

textBox2 = tkinter.Entry(width=10)
textBox2.place(x=135, y=starty+duration)

textBox3 = tkinter.Entry(width=10)
textBox3.place(x=135, y=starty+duration*2)

textBox4 = tkinter.Entry(width=10)
textBox4.place(x=135, y=starty+duration*3)

textBox5 = tkinter.Entry(width=10)
textBox5.place(x=135, y=starty+duration*4)

textBox6 = tkinter.Entry(width=10)
textBox6.place(x=135, y=starty+duration*5)

textBox7 = tkinter.Entry(width=10)
textBox7.place(x=135, y=starty+duration*6)

textBox8 = tkinter.Entry(width=10)
textBox8.place(x=135, y=starty+duration*7)



over_x = 240
below_x = 300


def onvar11():
    var11.set(True)
    var12.set(False)

def onvar12():
    var11.set(False)
    var12.set(True)

def onvar13():
    var13.set(True)
    var14.set(False)

def onvar14():
    var13.set(False)
    var14.set(True)

def onvar15():
    var15.set(True)
    var16.set(False)

def onvar16():
    var15.set(False)
    var16.set(True)


def onvar17():
    var17.set(True)
    var18.set(False)

def onvar18():
    var17.set(False)
    var18.set(True)

def onvar19():
    var19.set(True)
    var20.set(False)

def onvar20():
    var19.set(False)
    var20.set(True)

def onvar21():
    var21.set(True)
    var22.set(False)

def onvar22():
    var21.set(False)
    var22.set(True)

def onvar23():
    var23.set(True)
    var24.set(False)

def onvar24():
    var23.set(False)
    var24.set(True)

def onvar25():
    var25.set(True)
    var26.set(False)

def onvar26():
    var25.set(False)
    var26.set(True)



var11 = tkinter.BooleanVar()
chk11 = tkinter.Checkbutton(root, text='以上',variable=var11,command=onvar11)
chk11.place(x=over_x,y=starty)
var11.set(True)

var12 = tkinter.BooleanVar()
chk12 = tkinter.Checkbutton(root, text='以下',variable=var12,command=onvar12)
chk12.place(x=below_x,y=starty)

var13 = tkinter.BooleanVar()
chk13 = tkinter.Checkbutton(root, text='以上',variable=var13,command=onvar13)
chk13.place(x=over_x,y=starty+duration)
var13.set(True)

var14 = tkinter.BooleanVar()
chk14 = tkinter.Checkbutton(root, text='以下',variable=var14,command=onvar14)
chk14.place(x=below_x,y=starty+duration)

var15 = tkinter.BooleanVar()
chk15 = tkinter.Checkbutton(root, text='以上',variable=var15,command=onvar15)
chk15.place(x=over_x,y=starty+duration*2)

var15.set(True)

var16 = tkinter.BooleanVar()
chk16 = tkinter.Checkbutton(root, text='以下',variable=var16,command=onvar16)
chk16.place(x=below_x,y=starty+duration*2)

var17 = tkinter.BooleanVar()
chk17 = tkinter.Checkbutton(root, text='以上',variable=var17,command=onvar17)
chk17.place(x=over_x,y=starty+duration*3)

var17.set(True)

var18 = tkinter.BooleanVar()
chk18 = tkinter.Checkbutton(root, text='以下',variable=var18,command=onvar18)
chk18.place(x=below_x,y=starty+duration*3)

var19 = tkinter.BooleanVar()
chk19 = tkinter.Checkbutton(root, text='以上',variable=var19,command=onvar19)
chk19.place(x=over_x,y=starty+duration*4)

var19.set(True)

var20 = tkinter.BooleanVar()
chk20 = tkinter.Checkbutton(root, text='以下',variable=var20,command=onvar20)
chk20.place(x=below_x,y=starty+duration*4)

var21 = tkinter.BooleanVar()
chk21 = tkinter.Checkbutton(root, text='以上',variable=var21,command=onvar21)
chk21.place(x=over_x,y=starty+duration*5)

var21.set(True)

var22 = tkinter.BooleanVar()
chk22 = tkinter.Checkbutton(root, text='以下',variable=var22,command=onvar22)
chk22.place(x=below_x,y=starty+duration*5)

var23 = tkinter.BooleanVar()
chk23 = tkinter.Checkbutton(root, text='以上',variable=var23,command=onvar23)
chk23.place(x=over_x,y=starty+duration*6)

var23.set(True)

var24 = tkinter.BooleanVar()
chk24 = tkinter.Checkbutton(root, text='以下',variable=var24,command=onvar24)
chk24.place(x=below_x,y=starty+duration*6)

var25 = tkinter.BooleanVar()
chk25 = tkinter.Checkbutton(root, text='以上',variable=var25,command=onvar25)
chk25.place(x=over_x,y=starty+duration*7)

var25.set(True)

var26 = tkinter.BooleanVar()
chk26 = tkinter.Checkbutton(root, text='以下',variable=var26,command=onvar26)
chk26.place(x=below_x,y=starty+duration*7)


prime_var = tkinter.BooleanVar()
prime_chk = tkinter.Checkbutton(root, text='プライム',variable=prime_var)
prime_chk.place(x=190,y=starty+duration*7+60)
prime_var.set(True)

growth_var = tkinter.BooleanVar()
growth_chk = tkinter.Checkbutton(root, text='グロース',variable=growth_var)
growth_chk.place(x=30,y=starty+duration*7+60)
growth_var.set(True)


standard_var = tkinter.BooleanVar()
standard_chk = tkinter.Checkbutton(root, text='スタンダード',variable=standard_var)
standard_chk.place(x=100,y=starty+duration*7+60)
standard_var.set(True)


def on_ascend_var():
    ascend_var.set(True)
    descend_var.set(False)
    none_var.set(False)

def on_descend_var():
    ascend_var.set(False)
    descend_var.set(True)
    none_var.set(False)

def on_none_var():
    ascend_var.set(False)
    descend_var.set(False)
    none_var.set(True)


def on_buy_gradient_var():
    sort_buy_gradient_var.set(True)
    sort_buy_ratio_var.set(False)
    sort_buy_approximation_var.set(False)
    sort_buy_comparation_var.set(False)
    sort_sell_gradient_var.set(False)
    sort_sell_ratio_var.set(False)
    sort_sell_approximation_var.set(False)
    sort_sell_comparation_var.set(False)


def on_buy_ratio_var():
    sort_buy_gradient_var.set(False)
    sort_buy_ratio_var.set(True)
    sort_buy_approximation_var.set(False)
    sort_buy_comparation_var.set(False)
    sort_sell_gradient_var.set(False)
    sort_sell_ratio_var.set(False)
    sort_sell_approximation_var.set(False)
    sort_sell_comparation_var.set(False)

def on_buy_approximation_var():
    sort_buy_gradient_var.set(False)
    sort_buy_ratio_var.set(False)
    sort_buy_approximation_var.set(True)
    sort_buy_comparation_var.set(False)
    sort_sell_gradient_var.set(False)
    sort_sell_ratio_var.set(False)
    sort_sell_approximation_var.set(False)
    sort_sell_comparation_var.set(False)

def on_buy_comparation_var():
    sort_buy_gradient_var.set(False)
    sort_buy_ratio_var.set(False)
    sort_buy_approximation_var.set(False)
    sort_buy_comparation_var.set(True)
    sort_sell_gradient_var.set(False)
    sort_sell_ratio_var.set(False)
    sort_sell_approximation_var.set(False)
    sort_sell_comparation_var.set(False)


def on_sell_gradient_var():
    sort_sell_gradient_var.set(True)
    sort_sell_ratio_var.set(False)
    sort_sell_approximation_var.set(False)
    sort_sell_comparation_var.set(False)
    sort_buy_gradient_var.set(False)
    sort_buy_ratio_var.set(False)
    sort_buy_approximation_var.set(False)
    sort_buy_comparation_var.set(False)


def on_sell_ratio_var():
    sort_sell_gradient_var.set(False)
    sort_sell_ratio_var.set(True)
    sort_sell_approximation_var.set(False)
    sort_sell_comparation_var.set(False)
    sort_buy_gradient_var.set(False)
    sort_buy_ratio_var.set(False)
    sort_buy_approximation_var.set(False)
    sort_buy_comparation_var.set(False)


def on_sell_approximation_var():
    sort_sell_gradient_var.set(False)
    sort_sell_ratio_var.set(False)
    sort_sell_approximation_var.set(True)
    sort_sell_comparation_var.set(False)
    sort_buy_gradient_var.set(False)
    sort_buy_ratio_var.set(False)
    sort_buy_approximation_var.set(False)
    sort_buy_comparation_var.set(False)


def on_sell_comparation_var():
    sort_sell_gradient_var.set(False)
    sort_sell_ratio_var.set(False)
    sort_sell_approximation_var.set(False)
    sort_sell_comparation_var.set(True)
    sort_buy_gradient_var.set(False)
    sort_buy_ratio_var.set(False)
    sort_buy_approximation_var.set(False)
    sort_buy_comparation_var.set(False)




ascend_var = tkinter.BooleanVar()
ascend_chk = tkinter.Checkbutton(root, text='昇順',variable=ascend_var,command=on_ascend_var)
ascend_chk.place(x=30,y=starty+duration*7+120)


descend_var = tkinter.BooleanVar()
descend_chk = tkinter.Checkbutton(root, text='降順',variable=descend_var,command=on_descend_var)
descend_chk.place(x=100,y=starty+duration*7+120)

none_var = tkinter.BooleanVar()
none_chk = tkinter.Checkbutton(root, text='なし',variable=none_var,command=on_none_var)
none_chk.place(x=180,y=starty+duration*7+120)
none_var.set(True)





sort_buy_gradient_var = tkinter.BooleanVar()
sort_buy_gradient_chk = tkinter.Checkbutton(root, text='勾配(買)',variable=sort_buy_gradient_var,command=on_buy_gradient_var)
sort_buy_gradient_chk.place(x=30,y=starty+duration*7+150)
sort_buy_gradient_var.set(True)

sort_buy_ratio_var = tkinter.BooleanVar()
sort_buy_ratio_chk = tkinter.Checkbutton(root, text='直近比率(買)',variable=sort_buy_ratio_var,command=on_buy_ratio_var)
sort_buy_ratio_chk.place(x=110,y=starty+duration*7+150)

sort_buy_approximation_var = tkinter.BooleanVar()
sort_buy_approximation_chk = tkinter.Checkbutton(root, text='近似値(買)',variable=sort_buy_approximation_var,command=on_buy_approximation_var)
sort_buy_approximation_chk.place(x=220,y=starty+duration*7+150)

sort_buy_comparation_var = tkinter.BooleanVar()
sort_buy_comparation_chk = tkinter.Checkbutton(root, text='比較値(買)',variable=sort_buy_comparation_var,command=on_buy_comparation_var)
sort_buy_comparation_chk.place(x=300,y=starty+duration*7+150)

sort_sell_gradient_var = tkinter.BooleanVar()
sort_sell_gradient_chk = tkinter.Checkbutton(root, text='勾配(売)',variable=sort_sell_gradient_var,command=on_sell_gradient_var)
sort_sell_gradient_chk.place(x=30,y=starty+duration*7+180)

sort_sell_ratio_var = tkinter.BooleanVar()
sort_sell_ratio_chk = tkinter.Checkbutton(root, text='直近比率(売)',variable=sort_sell_ratio_var,command=on_sell_ratio_var)
sort_sell_ratio_chk.place(x=110,y=starty+duration*7+180)

sort_sell_approximation_var = tkinter.BooleanVar()
sort_sell_approximation_chk = tkinter.Checkbutton(root, text='近似値(売)',variable=sort_sell_approximation_var,command=on_sell_approximation_var)
sort_sell_approximation_chk.place(x=220,y=starty+duration*7+180)

sort_sell_comparation_var = tkinter.BooleanVar()
sort_sell_comparation_chk = tkinter.Checkbutton(root, text='差(売)',variable=sort_sell_comparation_var,command = on_sell_comparation_var)
sort_sell_comparation_chk.place(x=300,y=starty+duration*7+180)



label = tkinter.Label(root, text="保存ファイル名")
label.place(x=30,y=starty+duration*7+280)


filenamebox = tkinter.Entry(width=16)
filenamebox.place(x=135,y=starty+duration*7+280)



root.mainloop()