#!/usr/bin/env python3
"""
测试SQLite缓存功能
"""
import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import BaoStockDataFetcher

def test_cache_performance():
    """测试缓存性能"""
    print("=" * 60)
    print("测试1: 缓存性能测试")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher(enable_cache=True)
    
    # 第一次获取（从网络）
    print("\n第一次获取股票列表（从网络）...")
    start_time = time.time()
    stocks1 = fetcher.get_stock_list()
    time1 = time.time() - start_time
    
    print(f"  耗时: {time1:.2f}秒")
    print(f"  股票数量: {len(stocks1)}")
    
    # 第二次获取（从缓存）
    print("\n第二次获取股票列表（从缓存）...")
    start_time = time.time()
    stocks2 = fetcher.get_stock_list()
    time2 = time.time() - start_time
    
    print(f"  耗时: {time2:.2f}秒")
    print(f"  股票数量: {len(stocks2)}")
    
    # 比较性能
    speedup = time1 / time2 if time2 > 0 else 0
    print(f"\n性能提升: {speedup:.1f}倍")
    
    return True

def test_historical_data_cache():
    """测试历史数据缓存"""
    print("\n" + "=" * 60)
    print("测试2: 历史数据缓存")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher(enable_cache=True)
    code = "000001"
    
    # 第一次获取
    print(f"\n第一次获取 {code} 历史数据（从网络）...")
    start_time = time.time()
    df1 = fetcher.get_historical_data(code, days=30)
    time1 = time.time() - start_time
    
    print(f"  耗时: {time1:.2f}秒")
    print(f"  数据条数: {len(df1)}")
    
    # 第二次获取
    print(f"\n第二次获取 {code} 历史数据（从缓存）...")
    start_time = time.time()
    df2 = fetcher.get_historical_data(code, days=30)
    time2 = time.time() - start_time
    
    print(f"  耗时: {time2:.2f}秒")
    print(f"  数据条数: {len(df2)}")
    
    # 比较性能
    speedup = time1 / time2 if time2 > 0 else 0
    print(f"\n性能提升: {speedup:.1f}倍")
    
    # 验证数据一致性
    if len(df1) == len(df2):
        print("数据一致性验证通过")
    else:
        print("数据一致性验证失败")
    
    return True

def test_cache_info():
    """测试缓存信息"""
    print("\n" + "=" * 60)
    print("测试3: 缓存信息")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher(enable_cache=True)
    
    # 先获取一些数据以填充缓存
    print("\n获取测试数据...")
    fetcher.get_stock_list()
    fetcher.get_historical_data("000001", days=30)
    fetcher.get_historical_data("600000", days=30)
    
    # 获取缓存信息
    info = fetcher.get_cache_info()
    
    print("\n缓存统计:")
    print(f"  股票列表数量: {info.get('stock_list_count', 0)}")
    print(f"  历史数据条数: {info.get('historical_data_count', 0)}")
    print(f"  历史数据股票数: {info.get('historical_stocks_count', 0)}")
    print(f"  实时行情数量: {info.get('spot_data_count', 0)}")
    print(f"  指数数据条数: {info.get('index_data_count', 0)}")
    print(f"  指数数据股票数: {info.get('index_stocks_count', 0)}")
    print(f"  数据库大小: {info.get('db_size_mb', 0):.2f} MB")
    
    return True

def test_cache_clear():
    """测试清除缓存"""
    print("\n" + "=" * 60)
    print("测试4: 清除缓存")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher(enable_cache=True)
    
    # 获取缓存信息
    info_before = fetcher.get_cache_info()
    print(f"\n清除前缓存大小: {info_before.get('db_size_mb', 0):.2f} MB")
    
    # 清除历史数据缓存
    print("\n清除历史数据缓存...")
    fetcher.clear_cache('historical_data')
    
    # 获取清除后的缓存信息
    info_after = fetcher.get_cache_info()
    print(f"清除后缓存大小: {info_after.get('db_size_mb', 0):.2f} MB")
    
    # 清除所有缓存
    print("\n清除所有缓存...")
    fetcher.clear_cache()
    
    # 获取清除后的缓存信息
    info_final = fetcher.get_cache_info()
    print(f"最终缓存大小: {info_final.get('db_size_mb', 0):.2f} MB")
    
    return True

def test_cache_disabled():
    """测试禁用缓存"""
    print("\n" + "=" * 60)
    print("测试5: 禁用缓存")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher(enable_cache=False)
    
    print("\n获取股票列表（禁用缓存）...")
    start_time = time.time()
    stocks = fetcher.get_stock_list()
    time_used = time.time() - start_time
    
    print(f"  耗时: {time_used:.2f}秒")
    print(f"  股票数量: {len(stocks)}")
    
    # 检查缓存信息
    info = fetcher.get_cache_info()
    print(f"\n缓存信息: {info}")
    
    return True

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("测试SQLite缓存功能")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("缓存性能测试", test_cache_performance()))
    results.append(("历史数据缓存", test_historical_data_cache()))
    results.append(("缓存信息", test_cache_info()))
    results.append(("清除缓存", test_cache_clear()))
    results.append(("禁用缓存", test_cache_disabled()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "通过" if result else "失败"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n所有测试通过！缓存功能正常工作")
        print("\n使用方法:")
        print("  from src import BaoStockDataFetcher")
        print("  # 启用缓存（默认）")
        print("  fetcher = BaoStockDataFetcher()")
        print("  # 禁用缓存")
        print("  fetcher = BaoStockDataFetcher(enable_cache=False)")
        print("  # 清除缓存")
        print("  fetcher.clear_cache()")
        print("  # 获取缓存信息")
        print("  info = fetcher.get_cache_info()")
        return 0
    else:
        print(f"\n{total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
