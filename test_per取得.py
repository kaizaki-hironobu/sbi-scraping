import requests
from bs4 import BeautifulSoup
import re
import warnings
warnings.simplefilter("ignore")

ticker_code = "7203"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 銘柄ページから企業情報ページのコードを取得
ticker_url = f"https://irbank.net/{ticker_code}"
res = requests.get(ticker_url, headers=headers)
soup = BeautifulSoup(res.text, 'html.parser')

# 企業情報ページへのリンクを探す
links = soup.find_all('a', href=re.compile(r'/E\d+'))
company_code = links[0].get('href').strip('/')

# 企業情報ページを取得
company_url = f"https://irbank.net/{company_code}"
res = requests.get(company_url, headers=headers)
soup = BeautifulSoup(res.text, 'html.parser')

# PER関連の部分を抽出（HTML）
print("=== HTML内のPER関連部分 ===")
per_elements = soup.find_all(string=re.compile(r'PER'))
for elem in per_elements[:10]:  # 最初の10個まで
    print(f"要素: {elem}")
    if elem.parent:
        print(f"親要素: {elem.parent}")
        # 次の兄弟要素も確認
        if elem.parent.next_sibling:
            print(f"次の兄弟: {elem.parent.next_sibling}")
    print("-" * 60)

# テキスト化したものを確認
text = soup.get_text()
print("\n=== get_text()後のPER関連部分 ===")
# PERを含む行を抽出
lines = text.split('\n')
for i, line in enumerate(lines):
    if 'PER' in line:
        # 前後3行も含めて表示
        start = max(0, i-3)
        end = min(len(lines), i+4)
        print(f"行{i}周辺:")
        for j in range(start, end):
            marker = ">>> " if j == i else "    "
            print(f"{marker}{lines[j]}")
        print("-" * 60)
