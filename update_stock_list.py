from src.baostock_fetcher import BaoStockDataFetcher

print("重新获取股票列表（过滤掉退市股票）...")
fetcher = BaoStockDataFetcher()
stocks = fetcher.get_stock_list()

print(f"\n股票列表信息:")
print(f"  总股票数: {len(stocks)}")
print(f"  状态分布:")
print(stocks['status'].value_counts())

# 保存到缓存
from src.cache import StockDataCache
cache = StockDataCache()
cache.save_stock_list(stocks)
print(f"\n已更新股票列表到缓存")
