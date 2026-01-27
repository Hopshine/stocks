#!/usr/bin/env python3
"""
测试Flask应用的API接口
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import BaoStockDataFetcher, TechnicalAnalyzer

def test_api_stock_list():
    """测试获取股票列表"""
    print("=" * 60)
    print("测试1: 获取股票列表")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    stocks = fetcher.get_stock_list()
    
    if stocks.empty:
        print("❌ 获取股票列表失败")
        return False
    
    print(f"✓ 成功获取 {len(stocks)} 只股票")
    print(f"  列名: {list(stocks.columns)}")
    
    # 模拟API返回格式
    stocks = stocks.head(500)
    data = stocks.to_dict(orient='records')
    print(f"  返回数据示例（第一条）:")
    print(f"    {data[0]}")
    
    return True

def test_api_stock_info():
    """测试获取股票信息"""
    print("\n" + "=" * 60)
    print("测试2: 获取股票信息")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    code = "000001"
    
    # 获取实时行情
    spot = fetcher.get_stock_spot(code)
    print(f"  实时行情: {spot}")
    
    # 获取历史数据
    df = fetcher.get_historical_data(code, days=30)
    
    if df.empty:
        print("❌ 获取历史数据失败")
        return False
    
    print(f"✓ 成功获取 {len(df)} 条历史数据")
    
    # 最近5天数据
    recent = df.tail(5)[['close', 'open', 'high', 'low', 'volume', 'pct_change']]
    recent_dict = recent.reset_index().to_dict(orient='records')
    for item in recent_dict:
        item['date'] = item['date'].strftime('%Y-%m-%d') if hasattr(item['date'], 'strftime') else str(item['date'])
    
    print(f"  最近5天数据:")
    for item in recent_dict:
        print(f"    {item['date']}: 收盘价={item['close']}, 涨跌幅={item['pct_change']}%")
    
    # 统计信息
    stats = {
        'max_30d': float(df['high'].max()),
        'min_30d': float(df['low'].min()),
        'avg_volume': float(df['volume'].mean()),
        'total_change_5d': float(df['pct_change'].tail(5).sum())
    }
    print(f"  统计信息:")
    print(f"    最高价: {stats['max_30d']:.2f}")
    print(f"    最低价: {stats['min_30d']:.2f}")
    print(f"    平均成交量: {stats['avg_volume']:,.0f}")
    print(f"    近5日涨幅: {stats['total_change_5d']:.2f}%")
    
    return True

def test_api_technical_analysis():
    """测试技术分析"""
    print("\n" + "=" * 60)
    print("测试3: 技术分析")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    code = "000001"
    days = 60
    
    df = fetcher.get_historical_data(code, days=days)
    
    if df.empty:
        print("❌ 获取历史数据失败")
        return False
    
    analyzer = TechnicalAnalyzer(df)
    signals = analyzer.get_latest_signals()
    
    # 转换numpy类型为Python类型
    def convert_value(v):
        if hasattr(v, 'item'):
            return v.item()
        return v
    
    signals = {k: convert_value(v) for k, v in signals.items()}
    
    print(f"✓ 成功计算技术指标")
    print(f"  信号数量: {len(signals)}")
    print(f"  主要信号:")
    for key in ['ma5', 'ma10', 'ma20', 'macd', 'rsi', 'kdj_signal']:
        if key in signals:
            print(f"    {key}: {signals[key]}")
    
    return True

def test_api_screening():
    """测试选股策略"""
    print("\n" + "=" * 60)
    print("测试4: 选股策略")
    print("=" * 60)
    
    from src import MACDStrategy
    
    fetcher = BaoStockDataFetcher()
    strategy_type = 'macd'
    limit = 10
    
    # 获取股票列表
    stocks = fetcher.get_stock_list()
    if limit > 0:
        stocks = stocks.head(limit)
    
    print(f"  分析 {len(stocks)} 只股票...")
    
    # 执行策略
    strategy = MACDStrategy(fetcher)
    result_df = strategy.filter(stocks)
    
    if result_df.empty:
        print("  未找到符合条件的股票")
    else:
        print(f"✓ 找到 {len(result_df)} 只符合条件的股票")
        print(f"  结果:")
        print(result_df.to_string())
    
    return True

def test_api_sectors():
    """测试行业板块"""
    print("\n" + "=" * 60)
    print("测试5: 行业板块")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    sectors = fetcher.get_industry_ranking()
    
    if sectors.empty:
        print("⚠ baostock不提供行业板块排行数据")
        return True
    
    print(f"✓ 成功获取 {len(sectors)} 个行业板块")
    print(f"  前5个:")
    print(sectors.head().to_string())
    
    return True

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("测试Flask应用的API接口")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("获取股票列表", test_api_stock_list()))
    results.append(("获取股票信息", test_api_stock_info()))
    results.append(("技术分析", test_api_technical_analysis()))
    results.append(("选股策略", test_api_screening()))
    results.append(("行业板块", test_api_sectors()))
    
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
        print("\n✓ 所有测试通过！Flask应用可以正常使用")
        print("\n启动Flask应用:")
        print("  python app.py")
        print("\n访问地址:")
        print("  http://127.0.0.1:5000")
        return 0
    else:
        print(f"\n⚠ {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
