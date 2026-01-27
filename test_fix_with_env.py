#!/usr/bin/env python3
"""
测试修复后的data_fetcher模块 - 使用环境变量禁用代理
"""
import os
import sys

# 在导入任何模块之前，设置环境变量来禁用代理
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['ALL_PROXY'] = ''
os.environ['all_proxy'] = ''

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_fetcher import StockDataFetcher

def test_stock_list():
    """测试获取股票列表"""
    print("=" * 60)
    print("测试1: 获取股票列表")
    print("=" * 60)
    
    fetcher = StockDataFetcher()
    stocks = fetcher.get_stock_list()
    
    if stocks.empty:
        print("❌ 测试失败: 返回空DataFrame")
        print("   这可能是网络问题，请检查连接")
        return False
    else:
        print(f"✓ 测试通过: 成功获取 {len(stocks)} 只股票")
        print(f"  列名: {list(stocks.columns)}")
        print(f"  前3行数据:")
        print(stocks.head(3).to_string())
        return True

def test_single_stock():
    """测试获取单只股票数据"""
    print("\n" + "=" * 60)
    print("测试2: 获取单只股票历史数据 (000001 平安银行)")
    print("=" * 60)
    
    fetcher = StockDataFetcher()
    from datetime import datetime, timedelta
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    df = fetcher.get_historical_data("000001", start_date=start_date)
    
    if df.empty:
        print("❌ 测试失败: 返回空DataFrame")
        return False
    else:
        print(f"✓ 测试通过: 成功获取 {len(df)} 条历史数据")
        print(f"  列名: {list(df.columns)}")
        print(f"  最新数据:")
        print(df.tail(1).to_string())
        return True

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始测试修复后的data_fetcher模块")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("获取股票列表", test_stock_list()))
    results.append(("获取单只股票数据", test_single_stock()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n✓ 所有测试通过!")
        return 0
    else:
        print(f"\n⚠ {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
