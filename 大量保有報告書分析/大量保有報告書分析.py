import tkinter as tk
from tkinter import scrolledtext
import threading
import requests
from bs4 import BeautifulSoup
import re
import csv
import warnings
from datetime import datetime
warnings.simplefilter("ignore")

# 分析結果を保存するリスト
analysis_results = []


def get_market_segment(ticker_code):
    """
    銘柄コードから市場区分を取得
    戻り値: 'P', 'S', 'G', または None
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
                                return 'P'
                            elif '東証STD' in market_text or '東証2部' in market_text:
                                return 'S'
                            elif '東証GRT' in market_text or '東証JQS' in market_text:
                                return 'G'

    except Exception as e:
        pass

    return None


def get_company_name(ticker_code):
    """銘柄名を取得"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        url = f"https://irbank.net/{ticker_code}"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text()

        # 銘柄名を取得
        match = re.search(r'(\d{4})\s+(.+?)\s+\|', text)
        if match:
            return match.group(2)
    except:
        pass

    return None


def get_stock_price_on_date(ticker_code, target_date):
    """指定日の終値を取得"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        url = f"https://irbank.net/{ticker_code}/chart"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        table = soup.find('table')
        if not table:
            return None

        rows = table.find_all('tr')

        # target_dateをパース（YYYY/MM/DD形式）
        target_dt = datetime.strptime(target_date, '%Y/%m/%d')

        current_year = None
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) == 1:
                # 年の行
                year_text = cells[0].get_text().strip()
                if year_text.isdigit():
                    current_year = int(year_text)
                continue

            if len(cells) >= 5 and current_year:
                date_text = cells[0].get_text().strip()
                close_price_text = cells[4].get_text().strip()

                # 日付をパース（MM/DD形式）
                if '/' in date_text:
                    try:
                        month, day = map(int, date_text.split('/'))
                        row_date = datetime(current_year, month, day)

                        # 日付が一致するか確認
                        if row_date == target_dt:
                            if close_price_text and close_price_text != '':
                                price = float(re.sub(',', '', close_price_text))
                                return price
                    except:
                        continue
    except:
        pass

    return None


def get_current_stock_price(ticker_code):
    """現在の株価（直近の終値）を取得"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        url = f"https://irbank.net/{ticker_code}/chart"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        table = soup.find('table')
        if not table:
            return None

        rows = table.find_all('tr')

        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) == 1:
                continue

            if len(cells) >= 5:
                close_price_text = cells[4].get_text().strip()
                if close_price_text and close_price_text != '':
                    try:
                        price = float(re.sub(',', '', close_price_text))
                        return price
                    except:
                        continue
    except:
        pass

    return None


def get_large_holder_reports(ticker_code, output_text):
    """
    銘柄コードから大量保有報告書情報を取得してGUIに表示
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        output_text.insert(tk.END, f"\n{'='*100}\n")
        output_text.insert(tk.END, f"銘柄コード {ticker_code} の大量保有報告書分析を開始...\n")
        output_text.insert(tk.END, f"{'='*100}\n")
        output_text.see(tk.END)
        output_text.update()

        # 市場区分を取得
        market_segment = get_market_segment(ticker_code)
        if not market_segment:
            market_segment = '-'

        # 銘柄名を取得
        company_name = get_company_name(ticker_code)
        if not company_name:
            company_name = '取得失敗'

        # 現在の株価を取得
        current_price = get_current_stock_price(ticker_code)

        output_text.insert(tk.END, f"銘柄: {market_segment}-{company_name} ({ticker_code})\n")
        output_text.insert(tk.END, f"現在株価: {current_price:.2f}円\n" if current_price else "現在株価: 取得失敗\n")
        output_text.insert(tk.END, f"\n")
        output_text.see(tk.END)
        output_text.update()

        # karauri.netから大量保有報告書データを取得
        url = f"https://karauri.net/{ticker_code}/"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        # テーブルを探す（2番目のテーブルが大量保有報告書）
        tables = soup.find_all('table')
        if len(tables) < 2:
            output_text.insert(tk.END, "大量保有報告書データが見つかりません\n")
            output_text.see(tk.END)
            return

        holder_table = tables[1]
        rows = holder_table.find_all('tr')

        if len(rows) < 2:
            output_text.insert(tk.END, "大量保有報告書データがありません\n")
            output_text.see(tk.END)
            return

        # ヘッダー行をスキップしてデータ行を処理
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 6:
                continue

            # データ抽出
            date = cells[0].get_text().strip()  # ③日付
            institution = cells[1].get_text().strip()  # ④機関名
            ratio_text = cells[2].get_text().strip()  # ⑤株数（%）
            change_ratio_text = cells[3].get_text().strip()  # ⑥売買（%）
            shares_text = cells[4].get_text().strip()  # ⑦株数（数量）
            change_shares_text = cells[5].get_text().strip()  # ⑧売買（数量）

            # パーセントと数量を数値化
            ratio = ratio_text.replace('%', '').strip()
            change_ratio = change_ratio_text.replace('%', '').strip() if change_ratio_text else '0'

            # 株数の処理
            shares = re.sub(r'[株,]', '', shares_text).strip()
            change_shares = re.sub(r'[株,]', '', change_shares_text).strip() if change_shares_text else '0'

            # 数値変換
            try:
                change_ratio_num = float(change_ratio) if change_ratio else 0
            except:
                change_ratio_num = 0

            try:
                change_shares_num = int(change_shares) if change_shares else 0
            except:
                change_shares_num = 0

            # その日の終値を取得
            date_price = get_stock_price_on_date(ticker_code, date)

            # 株価変化率を計算（⑪）
            price_change_rate = None
            if date_price and current_price:
                price_change_rate = ((current_price - date_price) / date_price) * 100

            # ⑫ ⑧（変化株数）と⑪（株価変化率）が両方プラスなら「△」
            signal = ''
            if change_shares_num > 0 and price_change_rate and price_change_rate > 0:
                signal = '△'

            # 結果を横一列で表示（%と株を除去）
            ratio_display = ratio_text.replace('%', '')
            change_ratio_display = (change_ratio_text if change_ratio_text else '0').replace('%', '')
            shares_display = shares_text.replace('株', '').replace(',', '')
            change_shares_display = (change_shares_text if change_shares_text else '0').replace('株', '').replace(',', '')

            line = f"{ticker_code},{market_segment}-{company_name},{date},{institution},{ratio_display},{change_ratio_display},"
            line += f"{shares_display},{change_shares_display},"
            line += f"{date_price:.2f}," if date_price else "-,"
            line += f"{current_price:.2f}," if current_price else "-,"
            if price_change_rate is not None:
                line += f"{price_change_rate:+.2f},"
            else:
                line += "-,"
            line += f"{signal}\n"

            output_text.insert(tk.END, line, "normal")
            output_text.see(tk.END)
            output_text.update()

            # 結果をリストに保存
            result = {
                "Code": ticker_code,
                "Mkt/Name": f"{market_segment}-{company_name}",
                "Date": date,
                "Inst": institution,
                "Pos(%)": ratio_text,
                "ShortΔ(%)": change_ratio_text if change_ratio_text else '0%',
                "Pos(sh)": shares_text,
                "ShortΔ(sh)": change_shares_text if change_shares_text else '0',
                "Close": f"{date_price:.2f}" if date_price else "-",
                "Now": f"{current_price:.2f}" if current_price else "-",
                "Δ(%)": f"{price_change_rate:+.2f}%" if price_change_rate is not None else "-",
                "Flag": signal
            }
            analysis_results.append(result)

        output_text.insert(tk.END, f"{'='*100}\n")
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
    threading.Thread(target=get_large_holder_reports, args=(ticker_code, output_text)).start()


def on_clear_click():
    """クリアボタンクリック時の処理"""
    output_text.delete(1.0, tk.END)
    global analysis_results
    analysis_results = []


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
            fieldnames = ["Code", "Mkt/Name", "Date", "Inst", "Pos(%)", "ShortΔ(%)",
                         "Pos(sh)", "ShortΔ(sh)", "Close", "Now", "Δ(%)", "Flag"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(analysis_results)

        output_text.insert(tk.END, f"\n{len(analysis_results)}件のデータを {csv_filename} に保存しました\n\n")
        output_text.see(tk.END)
    except Exception as e:
        output_text.insert(tk.END, f"\nエラー: CSV保存に失敗しました - {e}\n\n")
        output_text.see(tk.END)


# メインウィンドウの作成
root = tk.Tk()
root.title("大量保有報告書分析ツール")
root.geometry("1000x750")

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

# 分析ボタン
analyze_button = tk.Button(input_frame, text="分析", width=10, command=on_analyze_click,
                          bg="#4CAF50", fg="#000000", activeforeground="#FFFFFF",
                          font=("Arial", 11, "bold"), relief=tk.RAISED, bd=2)
analyze_button.pack(side=tk.LEFT, padx=5)

# クリアボタン
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
output_text = scrolledtext.ScrolledText(root, width=100, height=30, font=("Menlo", 11),
                                       bg=TEXT_BG, fg=TEXT_FG, insertbackground=FG_COLOR)
output_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

# タグの設定（赤文字と緑文字）
output_text.tag_config("red", foreground="#ff4444")
output_text.tag_config("green", foreground="#44ff44")
output_text.tag_config("normal", foreground=TEXT_FG)

# 説明ラベル
info_label = tk.Label(root, text="銘柄コードを入力→分析→CSV保存",
                     font=("Arial", 10), bg=BG_COLOR, fg="#888888")
info_label.pack(pady=5)

# メインループ
root.mainloop()
