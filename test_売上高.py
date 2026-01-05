import requests
from bs4 import BeautifulSoup
import re
import warnings
warnings.simplefilter("ignore")


def get_revenue(ticker_code):
    """irbank.netから最新の売上高を取得"""
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

    # ステップ2: 業績ページから最新の売上高を取得
    results_url = f"https://irbank.net/{company_code}/results"
    print(f"URL: {results_url}")
    res = requests.get(results_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    # テーブルから売上高を取得
    # 最初のテーブルを探す
    table = soup.find('table')
    if not table:
        print(f"{ticker_code}: テーブルが見つかりません")
        return None

    # テーブルの行を取得
    rows = table.find_all('tr')

    if len(rows) < 2:
        print(f"{ticker_code}: データ行が見つかりません")
        return None

    # ヘッダー行を確認
    header_row = rows[0]
    headers = [cell.get_text().strip() for cell in header_row.find_all(['td', 'th'])]
    print(f"ヘッダー: {headers}")

    # 売上列のインデックスを探す
    revenue_col_index = None
    for i, header in enumerate(headers):
        if '売上' in header:
            revenue_col_index = i
            break

    if revenue_col_index is None:
        print(f"{ticker_code}: 売上列が見つかりません")
        return None

    # 最新期（最後から2番目の行、最後の行はヘッダーの重複の可能性）
    # データ行を探す（ヘッダーではない行）
    data_rows = []
    for row in rows[1:]:  # 最初のヘッダー行をスキップ
        cells = row.find_all(['td', 'th'])
        if cells and len(cells) > revenue_col_index:
            # ヘッダー行でない（年度が含まれている）
            year_text = cells[0].get_text().strip()
            if '年度' not in year_text and year_text:
                data_rows.append(row)

    if not data_rows:
        print(f"{ticker_code}: データ行が見つかりません")
        return None

    # 最新期（最後のデータ行）を取得
    latest_row = data_rows[-1]
    cells = latest_row.find_all(['td', 'th'])

    if len(cells) <= revenue_col_index:
        print(f"{ticker_code}: 売上データが見つかりません")
        return None

    revenue_text = cells[revenue_col_index].get_text().strip()
    print(f"最新期売上テキスト: {revenue_text}")

    # 「26.3兆」のようなパターンを解析
    # 兆円のパターン
    match = re.search(r'([0-9.]+)兆', revenue_text)
    if match:
        cho = float(match.group(1))
        revenue = int(cho * 1000000000000)
        print(f"{ticker_code} ({company_code}):")
        print(f"  売上高: {revenue:,}円 ({cho}兆円)")
        return revenue

    # 億円のパターン
    match = re.search(r'([0-9,]+)億', revenue_text)
    if match:
        oku_str = match.group(1)
        oku = float(re.sub(',', '', oku_str))
        revenue = int(oku * 100000000)
        print(f"{ticker_code} ({company_code}):")
        print(f"  売上高: {revenue:,}円 ({oku}億円)")
        return revenue

    # 百万円のパターン
    match = re.search(r'([0-9,]+)', revenue_text)
    if match:
        revenue_str = match.group(1)
        revenue_million = int(re.sub(',', '', revenue_str))
        revenue = revenue_million * 1000000
        print(f"{ticker_code} ({company_code}):")
        print(f"  売上高: {revenue:,}円 ({revenue_million:,}百万円)")
        return revenue

    print(f"{ticker_code}: 売上高のパターンが認識できません")

    return None


# テスト実行
if __name__ == "__main__":
    ticker_code = "7203"
    get_revenue(ticker_code)
