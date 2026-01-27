"""
基础使用示例 - 展示股票分析系统的基本功能
"""

import sys
sys.path.insert(0, '..')

from src import (
    StockDataFetcher,
    TechnicalAnalyzer,
    StockVisualizer,
    fetch_market_data,
    analyze_stock
)


def example_1_fetch_stock_data():
    """示例1: 获取股票数据"""
    print("=" * 60)
    print("示例1: 获取股票数据")
    print("=" * 60)
    
    fetcher = StockDataFetcher()
    
    # 获取单只股票历史数据
    df = fetcher.get_historical_data('000001', days=30)
    print(f"\n平安银行(000001) 近30日数据:")
    print(df.head())
    print(f"\n数据形状: {df.shape}")
    print(f"日期范围: {df.index[0]} 至 {df.index[-1]}")
    
    # 获取实时行情
    spot = fetcher.get_stock_spot('000001')
    print(f"\n实时行情:")
    for key, value in list(spot.items())[:10]:
        print(f"  {key}: {value}")
    
    # 获取全市场数据
    print("\n获取全市场数据...")
    market = fetcher.get_stock_list()
    print(f"共 {len(market)} 只股票")
    print(f"\n前5只股票:")
    print(market.head())


def example_2_technical_analysis():
    """示例2: 技术指标分析"""
    print("\n" + "=" * 60)
    print("示例2: 技术指标分析")
    print("=" * 60)
    
    # 获取数据
    fetcher = StockDataFetcher()
    df = fetcher.get_historical_data('600000', days=60)
    
    if df.empty:
        print("数据获取失败")
        return
    
    # 创建分析器
    analyzer = TechnicalAnalyzer(df)
    
    # 获取最新信号
    print("\n浦发银行(600000) 技术指标:")
    print("-" * 40)
    signals = analyzer.get_latest_signals()
    
    print(f"MA5:  {signals['ma5']:.2f}")
    print(f"MA10: {signals['ma10']:.2f}")
    print(f"MA20: {signals['ma20']:.2f}")
    print(f"MA60: {signals['ma60']:.2f}")
    print(f"\nMACD: {signals['macd']:.4f}")
    print(f"MACD Signal: {signals['macd_signal']}")
    print(f"\nRSI: {signals['rsi']:.2f}")
    print(f"RSI Signal: {signals['rsi_signal']}")
    print(f"\nKDJ: K={signals['k']:.2f}, D={signals['d']:.2f}, J={signals['j']:.2f}")
    print(f"KDJ Signal: {signals['kdj_signal']}")
    print(f"\nTrend: {signals['trend']}")
    
    # 计算所有指标
    print("\n所有技术指标 (最近5天):")
    all_indicators = analyzer.generate_signals()
    print(all_indicators[['ma5', 'ma10', 'ma20', 'rsi', 'macd', 'k', 'd']].tail())


def example_3_visualization():
    """示例3: 数据可视化"""
    print("\n" + "=" * 60)
    print("示例3: 数据可视化")
    print("=" * 60)
    
    # 获取数据
    fetcher = StockDataFetcher()
    df = fetcher.get_historical_data('000001', days=90)
    
    if df.empty:
        print("数据获取失败")
        return
    
    # 创建可视化器
    visualizer = StockVisualizer()
    
    # 绘制K线图
    print("\n绘制K线图...")
    # 注释掉以快速运行，取消注释可查看图表
    # visualizer.plot_kline(df, title="平安银行 - K线图")
    
    # 绘制技术指标图
    print("绘制技术指标图...")
    # visualizer.plot_with_indicators(
    #     df, 
    #     indicators=['ma', 'macd', 'rsi', 'boll'],
    #     title="平安银行 - 技术分析"
    # )
    
    print("可视化示例完成 (图表已注释，取消注释可查看)")


def example_4_quick_analysis():
    """示例4: 快速分析"""
    print("\n" + "=" * 60)
    print("示例4: 快速分析")
    print("=" * 60)
    
    # 使用便捷函数
    df = fetch_stock_data('000001', days=60)
    
    if df.empty:
        print("数据获取失败")
        return
    
    # 快速分析
    result = analyze_stock(df)
    
    print(f"\n平安银行快速分析结果:")
    print("-" * 40)
    for key, value in result.items():
        print(f"  {key}: {value}")


def example_5_multi_stock_analysis():
    """示例5: 多股分析对比"""
    print("\n" + "=" * 60)
    print("示例5: 多股分析对比")
    print("=" * 60)
    
    codes = ['000001', '600000', '600519']
    fetcher = StockDataFetcher()
    
    print("\n分析多只股票:")
    print("-" * 40)
    
    results = []
    for code in codes:
        df = fetcher.get_historical_data(code, days=30)
        if not df.empty:
            analyzer = TechnicalAnalyzer(df)
            signals = analyzer.get_latest_signals()
            results.append({
                'code': code,
                'latest_price': df['close'].iloc[-1],
                'change_pct': df['pct_change'].iloc[-1],
                'rsi': signals.get('rsi'),
                'trend': signals.get('trend')
            })
    
    import pandas as pd
    comparison = pd.DataFrame(results)
    print(comparison)


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("A股分析系统 - 基础使用示例")
    print("=" * 60)
    
    # 运行示例
    example_1_fetch_stock_data()
    example_2_technical_analysis()
    example_3_visualization()
    example_4_quick_analysis()
    example_5_multi_stock_analysis()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)
    print("\n提示: 取消example_3中的注释可查看图表")


if __name__ == "__main__":
    main()