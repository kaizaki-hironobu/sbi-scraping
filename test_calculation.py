import numpy as np

# 入力データ
major_holder_ratio = 0.474  # 大株主比率 47.4%
issued_stocks = 52_298_800  # 発行済株式数

# 浮動株数の計算
float_stocks = int(issued_stocks * (1 - major_holder_ratio))
print(f"浮動株数: {float_stocks:,}株")
print(f"浮動株数(10万株単位): {float_stocks/100000:.2f}")
print()

# 週次データ（古い順に並べる）
dates = [
    "04/28", "05/12", "05/19", "05/26", "06/02", "06/09", "06/16", "06/23", "06/30",
    "07/07", "07/14", "07/21", "07/28", "08/04", "08/10", "08/18", "08/25", "09/01", "09/08"
]

# 買い残データ（古い順）
buy_data = [
    5_252_700, 5_683_100, 5_294_100, 5_324_000, 5_646_500, 5_711_900, 6_045_200, 6_289_500, 6_356_400,
    6_944_200, 6_713_200, 6_908_600, 6_843_000, 6_521_200, 6_670_700, 6_545_000, 8_072_400, 8_149_000, 8_607_600
]

# 売り残+貸付残データ（古い順）
sell_data = [
    4_509_900, 6_581_800, 6_625_400, 7_720_200, 8_287_200, 9_040_300, 9_969_400, 9_325_400, 9_527_500,
    9_467_300, 9_406_900, 10_463_300, 11_108_950, 10_818_700, 10_045_600, 9_408_200, 12_369_750, 12_573_900, 13_394_900
]

data_length = len(dates)

print(f"データ期間: {dates[0]} ~ {dates[-1]}")
print(f"データ数: {data_length}週")
print()

# ========== 買い残の計算 ==========
print("=" * 60)
print("【買い残の計算】")
print("=" * 60)

# 10万株単位に変換
buy_data_100k = [x / 100000 for x in buy_data]

# 線形回帰
x = np.array(range(1, data_length + 1))
y = np.array(buy_data_100k)
a_buy, b_buy = np.polyfit(x, y, 1)

print(f"線形回帰式: y = {a_buy:.6f}x + {b_buy:.6f}")
print(f"  a (勾配): {a_buy:.6f}")
print(f"  b (切片): {b_buy:.6f}")
print()

# 勾配(買)
buy_gradient = a_buy
print(f"勾配(買): {buy_gradient:.6f}")

# 近似値(買)
buy_approximation = b_buy + a_buy * data_length
print(f"近似値(買): {buy_approximation:.6f} (10万株単位)")

# 直近比率(買) - 修正後
latest_buy = buy_data[-1]
buy_ratio = buy_data_100k[-1]  # 10万株単位
print(f"直近比率(買): {buy_ratio:.6f} (10万株単位)")
print(f"  最新の買い残: {latest_buy:,}株")
print(f"  計算式: {latest_buy:,} ÷ 100000 = {buy_ratio:.6f}")

# 差(買)
buy_difference = buy_ratio - buy_approximation
print(f"差(買): {buy_difference:.6f}")
print(f"  計算式: {buy_ratio:.6f} - {buy_approximation:.6f}")
print()

# ========== 売り残の計算 ==========
print("=" * 60)
print("【売り残の計算】")
print("=" * 60)

# 10万株単位に変換
sell_data_100k = [x / 100000 for x in sell_data]

# 線形回帰
y = np.array(sell_data_100k)
a_sell, b_sell = np.polyfit(x, y, 1)

print(f"線形回帰式: y = {a_sell:.6f}x + {b_sell:.6f}")
print(f"  a (勾配): {a_sell:.6f}")
print(f"  b (切片): {b_sell:.6f}")
print()

# 勾配(売)
sell_gradient = a_sell
print(f"勾配(売): {sell_gradient:.6f}")

# 近似値(売)
sell_approximation = b_sell + a_sell * data_length
print(f"近似値(売): {sell_approximation:.6f} (10万株単位)")

# 直近比率(売) - 修正後
latest_sell = sell_data[-1]
sell_ratio = sell_data_100k[-1]  # 10万株単位
print(f"直近比率(売): {sell_ratio:.6f} (10万株単位)")
print(f"  最新の売り残: {latest_sell:,}株")
print(f"  計算式: {latest_sell:,} ÷ 100000 = {sell_ratio:.6f}")

# 差(売)
sell_difference = sell_ratio - sell_approximation
print(f"差(売): {sell_difference:.6f}")
print(f"  計算式: {sell_ratio:.6f} - {sell_approximation:.6f}")
print()

# ========== まとめ ==========
print("=" * 60)
print("【計算結果まとめ】")
print("=" * 60)
print(f"浮動株数: {float_stocks:,}株")
print()
print(f"勾配(買):     {buy_gradient:.6f}")
print(f"近似値(買):   {buy_approximation:.6f} (10万株単位)")
print(f"直近比率(買): {buy_ratio:.6f} (10万株単位)")
print(f"差(買):       {buy_difference:.6f}")
print()
print(f"勾配(売):     {sell_gradient:.6f}")
print(f"近似値(売):   {sell_approximation:.6f} (10万株単位)")
print(f"直近比率(売): {sell_ratio:.6f} (10万株単位)")
print(f"差(売):       {sell_difference:.6f}")
