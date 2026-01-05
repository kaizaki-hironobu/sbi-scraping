import requests
from bs4 import BeautifulSoup
import re
import warnings
warnings.simplefilter("ignore")


def get_market_cap(ticker_code):
    """irbank.netから時価総額を取得"""
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

    # ステップ2: 企業情報ページから時価総額を取得
    company_url = f"https://irbank.net/{company_code}"
    res = requests.get(company_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    text = soup.get_text()

    # デバッグ: ページ内容を確認
    print(f"Company Code: {company_code}")
    print(f"URL: {company_url}")

    # 「時価53兆79億円」のようなパターンを検索
    match = re.search(r'時価([0-9]+)兆([0-9]+)億円', text)

    if match:
        cho = int(match.group(1))
        oku = int(match.group(2))
        market_cap = cho * 1000000000000 + oku * 100000000
        print(f"{ticker_code} ({company_code}):")
        print(f"  時価総額: {market_cap:,}円 ({cho}兆{oku}億円)")
        return market_cap

    # 億円単位のみの場合
    match = re.search(r'時価([0-9,]+)億円', text)
    if match:
        oku_str = match.group(1)
        oku = int(re.sub(',', '', oku_str))
        market_cap = oku * 100000000
        print(f"{ticker_code} ({company_code}):")
        print(f"  時価総額: {market_cap:,}円 ({oku}億円)")
        return market_cap

    # 百万円単位の場合
    match = re.search(r'時価総額([0-9,]+)百万円', text)
    if match:
        market_cap_str = match.group(1)
        market_cap_million = int(re.sub(',', '', market_cap_str))
        market_cap = market_cap_million * 1000000
        print(f"{ticker_code} ({company_code}):")
        print(f"  時価総額: {market_cap:,}円 ({market_cap_million}百万円)")
        return market_cap

    print(f"{ticker_code}: 時価総額が見つかりません")
    return None


# テスト実行
if __name__ == "__main__":
    ticker_code = "7203"
    get_market_cap(ticker_code)
