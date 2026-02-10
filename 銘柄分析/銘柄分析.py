import tkinter as tk
from tkinter import scrolledtext
import threading
import requests
from bs4 import BeautifulSoup
import re
import math
import csv
import warnings
warnings.simplefilter("ignore")

# 分析結果を保存するリスト
analysis_results = []


def get_market_segment(ticker_code):
    """
    銘柄コードから市場区分を取得
    戻り値: 'プレミアム', 'スタンダード', 'グロース', または None
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        url = f"https://karauri.net/{ticker_code}/"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        # テーブルを探す
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for i, row in enumerate(rows):
                # ヘッダー行で「主市場」を探す
                ths = row.find_all('th')
                if any('主市場' in th.get_text() for th in ths):
                    # 次の行にデータがある
                    if i + 1 < len(rows):
                        next_row = rows[i + 1]
                        first_td = next_row.find('td')
                        if first_td:
                            market_text = first_td.get_text().strip()

                            # 市場区分をマッピング
                            if '東証PRM' in market_text or '東証1部' in market_text:
                                return 'プライム'
                            elif '東証STD' in market_text or '東証2部' in market_text:
                                return 'スタンダード'
                            elif '東証GRT' in market_text or '東証JQS' in market_text:
                                return 'グロース'

    except Exception as e:
        pass  # GUIではエラーメッセージを出力しない

    return None


def get_stock_info(ticker_code, output_text):
    """
    銘柄コードから分析情報を取得してGUIに表示
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        output_text.insert(tk.END, f"\n{'='*60}\n")
        output_text.insert(tk.END, f"銘柄コード {ticker_code} の分析を開始...\n")
        output_text.insert(tk.END, f"{'='*60}\n")
        output_text.see(tk.END)
        output_text.update()

        # 市場区分を取得
        market_segment = get_market_segment(ticker_code)

        # ステップ1: 銘柄ページから企業情報ページのコードを取得
        ticker_url = f"https://irbank.net/{ticker_code}"
        res = requests.get(ticker_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 企業情報ページへのリンクを探す（E で始まるコード）
        links = soup.find_all('a', href=re.compile(r'/E\d+'))

        if not links:
            output_text.insert(tk.END, f"{ticker_code}: 企業情報ページへのリンクが見つかりません\n")
            output_text.see(tk.END)
            return None

        company_code = links[0].get('href').strip('/')

        # ステップ2: 企業情報ページから各種データを取得
        company_url = f"https://irbank.net/{company_code}"
        res = requests.get(company_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        text = soup.get_text()

        # 銘柄名を取得
        company_name = None
        match = re.search(r'(\d{4})\s+(.+?)\s+\|', text)
        if match:
            company_name = match.group(2)

        # 時価総額を取得
        market_cap = None
        match = re.search(r'時価([0-9]+)兆([0-9]+)億円', text)
        if match:
            cho = int(match.group(1))
            oku = int(match.group(2))
            market_cap = cho * 1000000000000 + oku * 100000000
        else:
            match = re.search(r'時価([0-9,]+)億円', text)
            if match:
                oku_str = match.group(1)
                oku = int(re.sub(',', '', oku_str))
                market_cap = oku * 100000000

        # 現在の株価を取得（直近1週間の終値の最高値）
        current_price = None
        chart_url = f"https://irbank.net/{ticker_code}/chart"
        res = requests.get(chart_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            prices = []
            count = 0
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) == 1:
                    continue
                if len(cells) >= 5:
                    close_price_text = cells[4].get_text().strip()
                    if close_price_text and close_price_text != '':
                        try:
                            price = float(re.sub(',', '', close_price_text))
                            prices.append(price)
                            count += 1
                            if count >= 7:
                                break
                        except ValueError:
                            continue

            if prices:
                current_price = max(prices)

        # PERを取得（「予」がついていないもの）
        per = None
        match = re.search(r'PER（連）([0-9.]+)倍PER（連）予', text)
        if match:
            per = float(match.group(1))

        # PSRを取得（時価総額 / 売上高で計算）
        psr = None

        # ステップ3: 業績ページから売上高を取得
        results_url = f"https://irbank.net/{company_code}/results"
        res = requests.get(results_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            if len(rows) >= 2:
                header_row = rows[0]
                headers_list = [cell.get_text().strip() for cell in header_row.find_all(['td', 'th'])]

                revenue_col_index = None
                for i, header in enumerate(headers_list):
                    if '売上' in header or '事業収益' in header or '収益' in header or '正味収入保険料' in header:
                        revenue_col_index = i
                        break

                if revenue_col_index is not None:
                    data_rows = []
                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        if cells and len(cells) > revenue_col_index:
                            year_text = cells[0].get_text().strip()
                            if '年度' not in year_text and year_text and '予' not in year_text:
                                data_rows.append(row)

                    # 最新の行から遡って、売上データがある行を探す
                    revenue = None
                    for latest_row in reversed(data_rows):
                        cells = latest_row.find_all(['td', 'th'])

                        if len(cells) > revenue_col_index:
                            revenue_text = cells[revenue_col_index].get_text().strip()

                            # '-'やハイフンのみ、または'0'の場合はスキップ
                            if revenue_text == '-' or revenue_text == '' or revenue_text == '0':
                                continue

                            match = re.search(r'([0-9.]+)兆', revenue_text)
                            if match:
                                cho = float(match.group(1))
                                revenue = int(cho * 1000000000000)
                                break
                            else:
                                match = re.search(r'([0-9,]+)億', revenue_text)
                                if match:
                                    oku_str = match.group(1)
                                    oku = float(re.sub(',', '', oku_str))
                                    revenue = int(oku * 100000000)
                                    break
                                else:
                                    # 百万単位に対応
                                    match = re.search(r'([0-9,]+)百万', revenue_text)
                                    if match:
                                        hyakuman_str = match.group(1)
                                        hyakuman = float(re.sub(',', '', hyakuman_str))
                                        revenue = int(hyakuman * 1000000)
                                        break

                    if market_cap and revenue and revenue > 0:
                        psr = market_cap / revenue

        # Zスコアを計算
        per_mean = 25
        per_std = 10
        psr_mean = 1.0  # 修正: PSR=0.9でZPSR≈-0.2になるように
        psr_std = 1.0   # 修正

        # 市場区分別の赤字ペナルティ定数
        penalty_constants = {
            'グロース': -0.8,
            'スタンダード': -1.2,
            'プレミアム': -2.0
        }

        zper = None
        zpsr = None

        # ZPERの計算（PERが黒字の場合はZスコア、赤字の場合はペナルティ定数）
        if per is not None:
            zper = (per - per_mean) / per_std
        else:
            # PERが赤字の場合、市場区分に応じたペナルティ定数を設定
            if market_segment in penalty_constants:
                zper = penalty_constants[market_segment]
            else:
                # 市場区分が不明な場合はスタンダードのペナルティを適用
                zper = penalty_constants['スタンダード']

        if psr is not None:
            zpsr = (psr - psr_mean) / psr_std

        # 適正株価を計算（ZPERとZPSRから計算）
        fair_price = None
        if zper is not None and zpsr is not None and current_price is not None:
            # Zスコアから標準化係数を計算
            # ZPER = (PER - per_mean) / per_std より PER = ZPER * per_std + per_mean
            # ただし、PERが赤字の場合はペナルティ定数なので、標準値を使用
            if per is not None:
                # 黒字の場合：通常の計算
                per_coefficient = per_mean / per
            else:
                # 赤字の場合：ZPERから仮想的なPER相当値を逆算
                # ZPERがマイナス（悪い）なので、補正係数は1より小さくなる
                virtual_per = zper * per_std + per_mean
                if virtual_per > 0:
                    per_coefficient = per_mean / virtual_per
                else:
                    # 極端に悪い場合は係数を小さく設定
                    per_coefficient = 0.5

            psr_coefficient = psr_mean / psr if psr and psr > 0 else 1.0
            total_coefficient = math.sqrt(per_coefficient * psr_coefficient)
            fair_price = current_price * total_coefficient

        # 変化率を計算（適正株価に対して現在株価がどれだけ乖離しているか）
        change_rate = None
        if fair_price is not None and current_price is not None and fair_price > 0:
            change_rate = ((current_price - fair_price) / fair_price) * 100

        # 結果を表示
        output_text.insert(tk.END, f"\n【銘柄分析結果】\n")
        output_text.insert(tk.END, f"1. 銘柄コード: {ticker_code}\n")
        output_text.insert(tk.END, f"2. 銘柄名: {company_name if company_name else '取得失敗'}\n")
        output_text.insert(tk.END, f"   市場区分: {market_segment if market_segment else '取得失敗'}\n")
        output_text.insert(tk.END, f"3. PER: {per if per else '赤字'}\n")
        output_text.insert(tk.END, f"4. PSR: {psr:.2f}\n" if psr else "4. PSR: 取得失敗\n")

        # ZPERの表示（赤字の場合はペナルティ定数を表示）
        if per is not None:
            output_text.insert(tk.END, f"5. ZPER: {zper:.2f} (基準: PER={per_mean}, 標準偏差={per_std})\n")
        else:
            output_text.insert(tk.END, f"5. ZPER: {zper:.2f} (赤字ペナルティ定数: {market_segment if market_segment else 'スタンダード'})\n")

        output_text.insert(tk.END, f"6. ZPSR: {zpsr:.2f} (基準: PSR={psr_mean}, 標準偏差={psr_std})\n" if zpsr is not None else "6. ZPSR: 取得失敗\n")
        output_text.insert(tk.END, f"7. PER,PSRから計算した適正株価: {fair_price:.2f}円\n" if fair_price is not None else "7. PER,PSRから計算した適正株価: 算出不可\n")
        output_text.insert(tk.END, f"8. 足元の株価: {current_price:.2f}円\n" if current_price is not None else "8. 足元の株価: 取得失敗\n")
        output_text.insert(tk.END, f"9. 変化率: {change_rate:+.2f}%\n" if change_rate is not None else "9. 変化率: 算出不可\n")
        output_text.insert(tk.END, f"{'='*60}\n\n")
        output_text.see(tk.END)

        # 結果をリストに保存
        result = {
            "銘柄コード": ticker_code,
            "銘柄名": company_name,
            "市場区分": market_segment,
            "PER": per,
            "PSR": psr,
            "ZPER": zper,
            "ZPSR": zpsr,
            "適正株価": fair_price,
            "現在株価": current_price,
            "変化率": change_rate
        }
        analysis_results.append(result)
        output_text.insert(tk.END, f"[データを保存しました。合計: {len(analysis_results)}件]\n\n")
        output_text.see(tk.END)

    except Exception as e:
        output_text.insert(tk.END, f"\nエラーが発生しました: {e}\n\n")
        output_text.see(tk.END)


def on_analyze_click():
    """分析ボタンクリック時の処理"""
    ticker_code = ticker_entry.get().strip()

    if not ticker_code:
        output_text.insert(tk.END, "\nエラー: 銘柄コードを入力してください\n\n")
        output_text.see(tk.END)
        return

    if not ticker_code.isdigit() or len(ticker_code) != 4:
        output_text.insert(tk.END, "\nエラー: 4桁の数字を入力してください\n\n")
        output_text.see(tk.END)
        return

    # 別スレッドで実行（UIをブロックしない）
    threading.Thread(target=get_stock_info, args=(ticker_code, output_text)).start()


def on_clear_click():
    """クリアボタンクリック時の処理"""
    output_text.delete(1.0, tk.END)


def on_save_csv_click():
    """CSV保存ボタンクリック時の処理"""
    if not analysis_results:
        output_text.insert(tk.END, "\nエラー: 保存するデータがありません\n\n")
        output_text.see(tk.END)
        return

    filename = filename_entry.get().strip()
    if not filename:
        output_text.insert(tk.END, "\nエラー: ファイル名を入力してください\n\n")
        output_text.see(tk.END)
        return

    csv_filename = f"{filename}.csv"
    try:
        with open(csv_filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["銘柄コード", "銘柄名", "市場区分", "PER", "PSR", "ZPER", "ZPSR", "適正株価", "現在株価", "変化率"])
            writer.writeheader()

            # 各結果を処理してCSVに出力
            for result in analysis_results:
                csv_row = {}
                for key, value in result.items():
                    if value is None:
                        # Noneの場合は「-」に変換
                        csv_row[key] = "-"
                    elif isinstance(value, float):
                        # 数値（float）の場合は小数点第2位まで丸める
                        csv_row[key] = round(value, 2)
                    else:
                        # その他（文字列、整数など）はそのまま
                        csv_row[key] = value
                writer.writerow(csv_row)

        output_text.insert(tk.END, f"\n{len(analysis_results)}件のデータを {csv_filename} に保存しました\n\n")
        output_text.see(tk.END)
    except Exception as e:
        output_text.insert(tk.END, f"\nエラー: CSV保存に失敗しました - {e}\n\n")
        output_text.see(tk.END)


# メインウィンドウの作成
root = tk.Tk()
root.title("銘柄分析ツール")
root.geometry("700x600")

# ダークモード対応の色設定
BG_COLOR = "#2b2b2b"
FG_COLOR = "#ffffff"
ENTRY_BG = "#404040"
ENTRY_FG = "#ffffff"
TEXT_BG = "#1e1e1e"
TEXT_FG = "#d4d4d4"

root.configure(bg=BG_COLOR)

# 銘柄コード入力欄
input_frame = tk.Frame(root, bg=BG_COLOR)
input_frame.pack(pady=10)

tk.Label(input_frame, text="銘柄コード（4桁）:", font=("Arial", 12), bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=5)
ticker_entry = tk.Entry(input_frame, width=10, font=("Arial", 12), bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=FG_COLOR)
ticker_entry.pack(side=tk.LEFT, padx=5)

# 分析ボタン（ボタンのテキスト色を確実に白に）
analyze_button = tk.Button(input_frame, text="分析", width=10, command=on_analyze_click,
                          bg="#4CAF50", fg="#000000", activeforeground="#FFFFFF",
                          font=("Arial", 11, "bold"), relief=tk.RAISED, bd=2)
analyze_button.pack(side=tk.LEFT, padx=5)

# クリアボタン（ボタンのテキスト色を確実に白に）
clear_button = tk.Button(input_frame, text="クリア", width=10, command=on_clear_click,
                        bg="#f44336", fg="#000000", activeforeground="#FFFFFF",
                        font=("Arial", 11, "bold"), relief=tk.RAISED, bd=2)
clear_button.pack(side=tk.LEFT, padx=5)

# CSV保存用フレーム
csv_frame = tk.Frame(root, bg=BG_COLOR)
csv_frame.pack(pady=5)

tk.Label(csv_frame, text="CSVファイル名:", font=("Arial", 12), bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=5)
filename_entry = tk.Entry(csv_frame, width=20, font=("Arial", 12), bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=FG_COLOR)
filename_entry.pack(side=tk.LEFT, padx=5)

# CSV保存ボタン
save_button = tk.Button(csv_frame, text="CSV保存", width=12, command=on_save_csv_click,
                       bg="#2196F3", fg="#000000", activeforeground="#FFFFFF",
                       font=("Arial", 11, "bold"), relief=tk.RAISED, bd=2)
save_button.pack(side=tk.LEFT, padx=5)

# 出力エリア（スクロール付きテキストボックス）
output_text = scrolledtext.ScrolledText(root, width=80, height=25, font=("Courier", 10), bg=TEXT_BG, fg=TEXT_FG, insertbackground=FG_COLOR)
output_text.pack(pady=10, padx=10)

# 説明ラベル
info_label = tk.Label(root, text="銘柄コードを入力→分析→複数分析後にCSVファイル名を入力→CSV保存", font=("Arial", 10), bg=BG_COLOR, fg="#888888")
info_label.pack(pady=5)

# メインループ
root.mainloop()
