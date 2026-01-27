#!/usr/bin/env python3
"""
测试baostock_fetcher与现有模块的兼容性
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import BaoStockDataFetcher, TechnicalAnalyzer

def test_baostock_fetcher():
    """测试baostock数据获取器"""
    print("=" * 60)
    print("测试1: BaoStockDataFetcher基本功能")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    
    # 测试获取股票列表
    print("\n1.1 获取股票列表...")
    stocks = fetcher.get_stock_list()
    if stocks.empty:
        print("❌ 获取股票列表失败")
        return False
    print(f"✓ 成功获取 {len(stocks)} 只股票")
    print(f"  前5行:")
    print(stocks.head())
    
    # 测试获取历史数据
    print("\n1.2 获取平安银行(000001)历史数据...")
    df = fetcher.get_historical_data("000001", days=30)
    if df.empty:
        print("❌ 获取历史数据失败")
        return False
    print(f"✓ 成功获取 {len(df)} 条历史数据")
    print(f"  列名: {list(df.columns)}")
    print(f"  最新5行:")
    print(df.tail())
    
    # 测试获取实时行情
    print("\n1.3 获取实时行情...")
    spot = fetcher.get_stock_spot("000001")
    if not spot:
        print("⚠ 获取实时行情失败（可能非交易日）")
    else:
        print(f"✓ 成功获取实时行情")
        for k, v in list(spot.items())[:5]:
            print(f"  {k}: {v}")
    
    return True

def test_technical_analysis_compatibility():
    """测试与技术分析模块的兼容性"""
    print("\n" + "=" * 60)
    print("测试2: 与TechnicalAnalyzer的兼容性")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    df = fetcher.get_historical_data("000001", days=60)
    
    if df.empty:
        print("❌ 获取历史数据失败")
        return False
    
    print("\n2.1 创建TechnicalAnalyzer...")
    analyzer = TechnicalAnalyzer(df)
    print("✓ 成功创建TechnicalAnalyzer")
    
    print("\n2.2 计算技术指标...")
    signals = analyzer.get_latest_signals()
    print("✓ 成功计算技术指标")
    print(f"  信号数量: {len(signals)}")
    print(f"  主要信号:")
    for key in ['ma5', 'ma10', 'ma20', 'macd', 'rsi']:
        if key in signals:
            print(f"    {key}: {signals[key]}")
    
    return True

def test_multiple_stocks():
    """测试多只股票数据获取"""
    print("\n" + "=" * 60)
    print("测试3: 多只股票数据获取")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    
    test_codes = ["000001", "000002", "600000", "600036"]
    
    for code in test_codes:
        print(f"\n获取 {code}...")
        df = fetcher.get_historical_data(code, days=30)
        if df.empty:
            print(f"  ✗ 失败")
        else:
            print(f"  ✓ 成功 - {len(df)} 条数据")
    
    return True

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("测试baostock_fetcher与现有模块的兼容性")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("BaoStockDataFetcher基本功能", test_baostock_fetcher()))
    results.append(("与TechnicalAnalyzer的兼容性", test_technical_analysis_compatibility()))
    results.append(("多只股票数据获取", test_multiple_stocks()))
    
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
        print("\n✓ 所有测试通过！baostock_fetcher可以正常使用")
        print("\n使用方法:")
        print("  from src import BaoStockDataFetcher")
        print("  fetcher = BaoStockDataFetcher()")
        print("  stocks = fetcher.get_stock_list()")
        print("  df = fetcher.get_historical_data('000001')")
        return 0
    else:
        print(f"\n⚠ {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
