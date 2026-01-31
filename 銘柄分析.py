import requests
from bs4 import BeautifulSoup
import re
import warnings
import csv
warnings.simplefilter("ignore")


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
                                return 'プレミアム'
                            elif '東証STD' in market_text or '東証2部' in market_text:
                                return 'スタンダード'
                            elif '東証GRT' in market_text or '東証JQS' in market_text:
                                return 'グロース'

    except Exception as e:
        print(f"市場区分取得エラー: {e}")

    return None


def get_stock_info(ticker_code):
    """
    銘柄コードから以下の情報を取得:
    1. 銘柄コード
    2. 銘柄名
    3. PER
    4. PSR
    5. ZPER (Zスコア化したPER)
    6. ZPSR (Zスコア化したPSR)
    7. PER,PSRから計算した時の株価
    8. 足元の株価
    9. 7と8の変化率
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # 市場区分を取得
    market_segment = get_market_segment(ticker_code)

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
        # ヘッダー行をスキップして、データ行を取得
        prices = []
        count = 0
        for row in rows[1:]:  # ヘッダーをスキップ
            cells = row.find_all(['td', 'th'])
            # 年の行（「2025」など）をスキップ
            if len(cells) == 1:
                continue
            # 終値（5列目、インデックス4）を取得
            if len(cells) >= 5:
                close_price_text = cells[4].get_text().strip()
                # カンマを除去して数値化
                if close_price_text and close_price_text != '':
                    try:
                        price = float(re.sub(',', '', close_price_text))
                        prices.append(price)
                        count += 1
                        if count >= 7:  # 7日分取得
                            break
                    except ValueError:
                        continue

        # 最高値を取得
        if prices:
            current_price = max(prices)

    # PERを取得（「予」がついていないもの）
    # テキスト内で「PER（連）9.18倍」のようなパターンを探す（「予」の前にあるもの）
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
                if '売上' in header:
                    revenue_col_index = i
                    break

            if revenue_col_index is not None:
                data_rows = []
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if cells and len(cells) > revenue_col_index:
                        year_text = cells[0].get_text().strip()
                        if '年度' not in year_text and year_text:
                            data_rows.append(row)

                if data_rows:
                    latest_row = data_rows[-1]
                    cells = latest_row.find_all(['td', 'th'])

                    if len(cells) > revenue_col_index:
                        revenue_text = cells[revenue_col_index].get_text().strip()

                        # 売上高を数値化
                        revenue = None
                        match = re.search(r'([0-9.]+)兆', revenue_text)
                        if match:
                            cho = float(match.group(1))
                            revenue = int(cho * 1000000000000)
                        else:
                            match = re.search(r'([0-9,]+)億', revenue_text)
                            if match:
                                oku_str = match.group(1)
                                oku = float(re.sub(',', '', oku_str))
                                revenue = int(oku * 100000000)

                        # PSRを計算
                        if market_cap and revenue and revenue > 0:
                            psr = market_cap / revenue

    # Zスコアを計算
    # 基準値と標準偏差の設定
    per_mean = 25  # 平均PER
    per_std = 10   # PERの標準偏差
    psr_mean = 1.0  # 平均PSR（修正: PSR=0.9でZPSR≈-0.2になるように）
    psr_std = 1.0   # PSRの標準偏差（修正）

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

        # 総合調整係数（幾何平均）
        import math
        total_coefficient = math.sqrt(per_coefficient * psr_coefficient)

        # 適正株価
        fair_price = current_price * total_coefficient

    # 変化率を計算
    change_rate = None
    if fair_price is not None and current_price is not None and current_price > 0:
        change_rate = ((fair_price - current_price) / current_price) * 100

    # 結果を表示
    print(f"\n{'='*60}")
    print(f"銘柄分析結果")
    print(f"{'='*60}")
    print(f"1. 銘柄コード: {ticker_code}")
    print(f"2. 銘柄名: {company_name if company_name else '取得失敗'}")
    print(f"   市場区分: {market_segment if market_segment else '取得失敗'}")
    print(f"3. PER: {per if per else '赤字'}")
    print(f"4. PSR: {psr:.2f}" if psr else "4. PSR: 取得失敗")

    # ZPERの表示（赤字の場合はペナルティ定数を表示）
    if per is not None:
        print(f"5. ZPER: {zper:.2f} (基準: PER={per_mean}, 標準偏差={per_std})")
    else:
        print(f"5. ZPER: {zper:.2f} (赤字ペナルティ定数: {market_segment if market_segment else 'スタンダード'})")

    print(f"6. ZPSR: {zpsr:.2f} (基準: PSR={psr_mean}, 標準偏差={psr_std})" if zpsr is not None else "6. ZPSR: 取得失敗")
    print(f"7. PER,PSRから計算した適正株価: {fair_price:.2f}円" if fair_price is not None else "7. PER,PSRから計算した適正株価: 取得失敗")
    print(f"8. 足元の株価: {current_price:.2f}円" if current_price is not None else "8. 足元の株価: 取得失敗")
    print(f"9. 変化率: {change_rate:+.2f}%" if change_rate is not None else "9. 変化率: 取得失敗")
    print(f"{'='*60}\n")

    return {
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


if __name__ == "__main__":
    # UIループ
    print("\n銘柄分析プログラム")
    print("=" * 60)

    results = []  # 結果を保存するリスト

    while True:
        ticker_code = input("\n銘柄コード（4桁）を入力してください（CSV出力は 's'、終了は 'q'）: ").strip()

        if ticker_code.lower() == 'q':
            print("プログラムを終了します。")
            break

        if ticker_code.lower() == 's':
            # CSV出力
            if not results:
                print("エラー: 保存するデータがありません。")
                continue

            filename = input("CSVファイル名を入力してください（拡張子なし）: ").strip()
            if not filename:
                print("エラー: ファイル名を入力してください。")
                continue

            csv_filename = f"{filename}.csv"
            try:
                with open(csv_filename, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["銘柄コード", "銘柄名", "市場区分", "PER", "PSR", "ZPER", "ZPSR", "適正株価", "現在株価", "変化率"])
                    writer.writeheader()
                    writer.writerows(results)
                print(f"\n{len(results)}件のデータを {csv_filename} に保存しました。\n")
            except Exception as e:
                print(f"エラー: CSV保存に失敗しました - {e}")
            continue

        if not ticker_code.isdigit() or len(ticker_code) != 4:
            print("エラー: 4桁の数字を入力してください。")
            continue

        try:
            result = get_stock_info(ticker_code)
            if result:
                results.append(result)
                print(f"\n[データを保存しました。合計: {len(results)}件]")
        except Exception as e:
            print(f"エラーが発生しました: {e}")
