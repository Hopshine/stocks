from src.baostock_fetcher import BaoStockDataFetcher
from src.cache import StockDataCache

print("强制重新获取股票列表（清除缓存）...")
cache = StockDataCache()
cache.clear_cache('stock_list')

fetcher = BaoStockDataFetcher()
stocks = fetcher.get_stock_list()

print(f"\n股票列表信息:")
print(f"  总股票数: {len(stocks)}")
print(f"  状态分布:")
print(stocks['status'].value_counts())

print(f"\n已更新股票列表到缓存")
