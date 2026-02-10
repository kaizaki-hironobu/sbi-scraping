import requests
from bs4 import BeautifulSoup
import re
import time
import warnings
import csv
warnings.simplefilter("ignore")


def get_issued_stocks(ticker_code):
    """irbank.netから発行済株式数を取得"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # ステップ1: 銘柄ページから企業情報ページのコードを取得
    ticker_url = f"https://irbank.net/{ticker_code}"
    res = requests.get(ticker_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    # 企業情報ページへのリンクを探す（E で始まるコード）
    links = soup.find_all('a', href=re.compile(r'/E\d+'))

    if not links:
        print(f"{ticker_code}: 企業情報ページへのリンクが見つかりません")
        return None

    company_code = links[0].get('href').strip('/')

    # ステップ2: 企業情報ページから発行済株式数を取得
    company_url = f"https://irbank.net/{company_code}"
    res = requests.get(company_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    text = soup.get_text()

    # 「発行済み株式総数」のパターンを検索
    match = re.search(r'発行済み?株式総数([0-9,]+)株', text)

    if match:
        issued_str = match.group(1)
        # カンマを除去
        issued_num = int(re.sub(',', '', issued_str))
        return issued_num
    else:
        print(f"{ticker_code}: 発行済株式数が見つかりません")
        return None


def get_major_holder_ratio(ticker_code):
    """irbank.netから大株主保有比率合計を取得"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    res = requests.get(f"https://irbank.net/{ticker_code}/holder", headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    try:
        # 大株主保有比率の合計を取得
        # irbank.netの構造: 1行目がヘッダー、2行目以降が大株主データ
        rows = soup.find_all("tr")
        total_ratio = 0.0

        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:  # 最低2列（株主名、最新期データ）
                # 2列目（cells[1]）に最新期の「順位+保有比率」がある（例：1位13.35%）
                ratio_text = cells[1].get_text().strip()

                # 「1位13.35%」から「13.35」を抽出
                match = re.search(r'(\d+(?:\.\d+)?)%', ratio_text)
                if match:
                    ratio = float(match.group(1))
                    total_ratio += ratio

        # パーセントから小数に変換（例: 45.5% → 0.455）
        return total_ratio / 100.0

    except Exception as e:
        print(f"{ticker_code}: 大株主保有比率の取得に失敗 - {e}")
        return None


# stocks.txtから銘柄コード一覧を読み込み
with open("stocks.txt") as f:
    text = f.read()
    tickers = text.split("\n")

# データを格納するリスト
datas = []

print(f"全{len(tickers)}銘柄のデータ取得を開始します...")

# 各銘柄のデータを取得
for i, ticker in enumerate(tickers, 1):
    if not ticker.strip():  # 空行はスキップ
        continue

    try:
        print(f"[{i}/{len(tickers)}] {ticker} を処理中...")

        # 発行済株式数を取得
        issued_stocks = get_issued_stocks(ticker)
        if issued_stocks is None:
            continue

        # 待機時間（サーバー負荷軽減）
        time.sleep(0.5)

        # 大株主保有比率合計を取得
        major_holder_ratio = get_major_holder_ratio(ticker)
        if major_holder_ratio is None:
            continue

        # 浮動株数を計算: 発行済株式数 × (1 - 大株主保有比率合計)
        float_stocks = int(issued_stocks * (1 - major_holder_ratio))

        print(f"  → 発行済: {issued_stocks:,}, 大株主比率: {major_holder_ratio:.2%}, 浮動株数: {float_stocks:,}")

        datas.append({
            "銘柄コード": ticker,
            "発行済株式数": issued_stocks,
            "大株主保有比率合計": round(major_holder_ratio, 4),
            "浮動株数": float_stocks
        })

        # 待機時間（サーバー負荷軽減）
        time.sleep(0.5)

    except Exception as e:
        print(f"{ticker}: エラー - {e}")
        continue

# CSV形式で保存
with open("float_data.csv", "w", encoding="utf-8", newline="") as f:
    if datas:
        writer = csv.DictWriter(f, fieldnames=["銘柄コード", "発行済株式数", "大株主保有比率合計", "浮動株数"])
        writer.writeheader()
        writer.writerows(datas)

print(f"\n取得が完了しました。{len(datas)}銘柄のデータをfloat_data.csvに保存しました。")
