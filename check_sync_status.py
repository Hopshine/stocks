from src.cache import StockDataCache

cache = StockDataCache()
info = cache.get_cache_info()

print("缓存信息:")
print(f"  股票列表: {info['stock_list_count']} 只")
print(f"  实时行情: {info['spot_data_count']} 只")
print(f"  历史数据: {info['historical_data_count']} 条")
print(f"  数据库大小: {info['db_size_mb']:.2f} MB")

# 计算失败数量
total_stocks = 3742
failed_count = total_stocks - info['spot_data_count']
print(f"\n同步状态:")
print(f"  总股票数: {total_stocks}")
print(f"  成功数量: {info['spot_data_count']}")
print(f"  失败数量: {failed_count}")
print(f"  成功率: {info['spot_data_count'] / total_stocks * 100:.1f}%")
