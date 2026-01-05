import requests
from bs4 import BeautifulSoup
import re
import warnings
warnings.simplefilter("ignore")

ticker_code = "7203"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 株価推移ページを取得
chart_url = f"https://irbank.net/{ticker_code}/chart"
print(f"URL: {chart_url}")
res = requests.get(chart_url, headers=headers)
soup = BeautifulSoup(res.text, 'html.parser')

# テーブルを探す
table = soup.find('table')
if table:
    print("テーブルが見つかりました")
    rows = table.find_all('tr')
    print(f"行数: {len(rows)}")

    # 最初の10行を表示
    for i, row in enumerate(rows[:10]):
        cells = row.find_all(['td', 'th'])
        print(f"行{i}: {[cell.get_text().strip() for cell in cells]}")
else:
    print("テーブルが見つかりません")
    # ページ内容の一部を表示
    text = soup.get_text()
    print("ページ内容サンプル:")
    print(text[:1000])
