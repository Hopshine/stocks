from src.data_sync import DataSyncService

print("=" * 60)
print("测试失败股票重试机制")
print("=" * 60)

service = DataSyncService()

# 测试同步实时行情（全量）
print("\n开始同步所有股票的实时行情（包含重试机制）...")
result = service.sync_market_data()

print("\n" + "=" * 60)
print("同步结果")
print("=" * 60)
print(f"成功: {result['success']}")
print(f"总股票数: {result['total_stocks']}")
print(f"成功数量: {result['success_count']}")
print(f"失败数量: {result['failed_count']}")
print(f"耗时: {result['duration_seconds']:.2f}秒")
print(f"成功率: {result['success_count'] / result['total_stocks'] * 100:.2f}%")

if result['errors']:
    print(f"\n错误信息（最多显示10个）:")
    for error in result['errors'][:10]:
        print(f"  - {error}")

# 检查缓存信息
print("\n" + "=" * 60)
print("缓存信息")
print("=" * 60)
cache_info = service.cache.get_cache_info()
print(f"股票列表: {cache_info['stock_list_count']} 只")
print(f"实时行情: {cache_info['spot_data_count']} 只")
print(f"历史数据: {cache_info['historical_data_count']} 条")
print(f"数据库大小: {cache_info['db_size_mb']:.2f} MB")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
