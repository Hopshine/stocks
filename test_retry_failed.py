from src.cache import StockDataCache
from src.baostock_fetcher import BaoStockDataFetcher

cache = StockDataCache()
fetcher = BaoStockDataFetcher()

# 获取所有股票
stocks = fetcher.get_stock_list()
all_codes = set(stocks['code'].tolist())

# 获取有缓存的股票
import sqlite3
conn = sqlite3.connect("data/stock_cache.db")
cursor = conn.cursor()
cursor.execute("SELECT code FROM spot_data")
cached_codes = set(row[0] for row in cursor.fetchall())
conn.close()

# 找出失败的股票
failed_codes = list(all_codes - cached_codes)
print(f"总股票数: {len(all_codes)}")
print(f"有缓存的股票数: {len(cached_codes)}")
print(f"失败的股票数: {len(failed_codes)}")
print(f"\n失败的股票列表（前20个）:")
for code in failed_codes[:20]:
    print(f"  {code}")

if len(failed_codes) > 0:
    print(f"\n测试重试失败的股票...")
    result = fetcher.get_batch_spot_data(failed_codes)
    print(f"重试成功: {len(result)}/{len(failed_codes)} 只")
