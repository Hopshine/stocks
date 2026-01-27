#!/usr/bin/env python3
"""
使用baostock获取A股数据的示例
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src import BaoStockDataFetcher, TechnicalAnalyzer, StockVisualizer

def example1_get_stock_list():
    """示例1: 获取股票列表"""
    print("=" * 60)
    print("示例1: 获取A股股票列表")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    stocks = fetcher.get_stock_list()
    
    print(f"\n共获取 {len(stocks)} 只股票")
    print("\n前10只股票:")
    print(stocks.head(10).to_string())
    
    # 统计各市场股票数量
    print(f"\n市场分布:")
    print(stocks['market'].value_counts())

def example2_get_historical_data():
    """示例2: 获取单只股票历史数据"""
    print("\n" + "=" * 60)
    print("示例2: 获取平安银行(000001)历史数据")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    df = fetcher.get_historical_data("000001", days=60)
    
    print(f"\n获取 {len(df)} 条历史数据")
    print("\n最新10天数据:")
    print(df.tail(10)[['close', 'volume', 'pct_change']].to_string())
    
    # 基本统计
    print(f"\n统计信息:")
    print(f"  最高价: {df['high'].max():.2f}")
    print(f"  最低价: {df['low'].min():.2f}")
    print(f"  平均成交量: {df['volume'].mean():,.0f}")
    print(f"  近5日涨幅: {df['pct_change'].tail(5).sum():.2f}%")

def example3_technical_analysis():
    """示例3: 技术分析"""
    print("\n" + "=" * 60)
    print("示例3: 技术分析")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    df = fetcher.get_historical_data("000001", days=60)
    
    analyzer = TechnicalAnalyzer(df)
    signals = analyzer.get_latest_signals()
    
    print("\n技术指标:")
    print(f"  MA5:  {signals.get('ma5', 'N/A'):.2f}")
    print(f"  MA10: {signals.get('ma10', 'N/A'):.2f}")
    print(f"  MA20: {signals.get('ma20', 'N/A'):.2f}")
    print(f"  MACD: {signals.get('macd', 'N/A'):.4f}")
    print(f"  MACD信号: {signals.get('macd_signal', 'N/A')}")
    print(f"  RSI:  {signals.get('rsi', 'N/A'):.2f}")
    print(f"  RSI信号: {signals.get('rsi_signal', 'N/A')}")
    print(f"  趋势: {signals.get('trend', 'N/A')}")

def example4_multiple_stocks():
    """示例4: 多只股票对比"""
    print("\n" + "=" * 60)
    print("示例4: 多只股票对比")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    
    stocks = [
        ("000001", "平安银行"),
        ("000002", "万科A"),
        ("600000", "浦发银行"),
        ("600036", "招商银行")
    ]
    
    print("\n股票表现对比（近30日）:")
    print(f"{'代码':<10} {'名称':<10} {'最新价':>10} {'涨跌幅':>10}")
    print("-" * 45)
    
    for code, name in stocks:
        df = fetcher.get_historical_data(code, days=30)
        if not df.empty:
            latest_price = df['close'].iloc[-1]
            total_change = df['pct_change'].sum()
            print(f"{code:<10} {name:<10} {latest_price:>10.2f} {total_change:>10.2f}%")

def example5_screening():
    """示例5: 简单选股"""
    print("\n" + "=" * 60)
    print("示例5: 简单选股 - 查找近期涨幅较大的股票")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    
    # 获取一些热门股票
    test_codes = ["000001", "000002", "000858", "600000", "600036", "600519", "000858"]
    
    results = []
    for code in test_codes:
        df = fetcher.get_historical_data(code, days=20)
        if not df.empty:
            latest_price = df['close'].iloc[-1]
            total_change = df['pct_change'].sum()
            avg_volume = df['volume'].mean()
            
            # 简单筛选条件：近20日涨幅>5%且平均成交量>100万
            if total_change > 5 and avg_volume > 1000000:
                results.append({
                    'code': code,
                    'price': latest_price,
                    'change': total_change,
                    'volume': avg_volume
                })
    
    if results:
        print(f"\n找到 {len(results)} 只符合条件的股票:")
        print(f"{'代码':<10} {'最新价':>10} {'近20日涨幅':>12} {'平均成交量':>15}")
        print("-" * 50)
        for r in results:
            print(f"{r['code']:<10} {r['price']:>10.2f} {r['change']:>12.2f}% {r['volume']:>15,.0f}")
    else:
        print("\n未找到符合条件的股票")

def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("baostock A股数据获取示例")
    print("=" * 60)
    
    try:
        example1_get_stock_list()
        example2_get_historical_data()
        example3_technical_analysis()
        example4_multiple_stocks()
        example5_screening()
        
        print("\n" + "=" * 60)
        print("所有示例运行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
