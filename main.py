#!/usr/bin/env python3
"""
A股分析系统 - 主程序

提供交互式命令行界面，方便用户进行股票分析和选股
"""

import sys
import argparse
from datetime import datetime
from typing import Optional

from src import (
    StockDataFetcher,
    TechnicalAnalyzer,
    StockVisualizer,
    MACDStrategy,
    RSIStrategy,
    GoldenCrossStrategy,
    VolumeBreakoutStrategy,
    MultiIndicatorStrategy,
    FundamentalStrategy
)


class StockAnalyzerCLI:
    """股票分析命令行界面"""
    
    def __init__(self):
        self.fetcher = StockDataFetcher()
        self.visualizer = StockVisualizer()
        self.running = True
    
    def print_menu(self):
        """打印主菜单"""
        print("\n" + "="*50)
        print("          A股分析系统 v1.0")
        print("="*50)
        print("  1. 查看股票列表")
        print("  2. 查询单只股票行情")
        print("  3. 股票技术分析")
        print("  4. 绘制K线图")
        print("  5. 选股策略")
        print("  6. 行业板块分析")
        print("  7. 概念板块分析")
        print("  0. 退出程序")
        print("="*50)
    
    def get_input(self, prompt: str) -> str:
        """获取用户输入"""
        return input(prompt).strip()
    
    def show_stock_list(self):
        """显示股票列表"""
        print("\n正在获取股票列表...")
        stocks = self.fetcher.get_stock_list()
        
        if stocks.empty:
            print("获取失败，请检查网络连接")
            return
        
        print(f"\n共获取 {len(stocks)} 只股票")
        print(f"\n涨幅前10名:")
        top_gainers = stocks.nlargest(10, 'change_pct')
        print(top_gainers[['code', 'name', 'price', 'change_pct', 'industry']].to_string())
        
        print(f"\n跌幅前10名:")
        top_losers = stocks.nsmallest(10, 'change_pct')
        print(top_losers[['code', 'name', 'price', 'change_pct', 'industry']].to_string())
    
    def query_single_stock(self):
        """查询单只股票"""
        code = self.get_input("请输入股票代码 (如: 000001): ")
        if not code:
            print("股票代码不能为空")
            return
        
        print(f"\n正在查询股票 {code}...")
        
        # 获取实时行情
        spot = self.fetcher.get_stock_spot(code)
        if spot:
            print("\n实时行情:")
            for key, value in spot.items():
                print(f"  {key}: {value}")
        else:
            print("获取实时行情失败")
        
        # 获取历史数据
        df = self.fetcher.get_historical_data(code, days=30)
        if not df.empty:
            print(f"\n近30日行情统计:")
            print(f"  最高价: {df['high'].max():.2f}")
            print(f"  最低价: {df['low'].min():.2f}")
            print(f"  平均成交量: {df['volume'].mean():.0f}")
            print(f"  近5日涨幅: {df['pct_change'].tail(5).sum():.2f}%")
    
    def technical_analysis(self):
        """股票技术分析"""
        code = self.get_input("请输入股票代码: ")
        if not code:
            return
        
        days = self.get_input("分析天数 (默认60): ") or "60"
        try:
            days = int(days)
        except ValueError:
            days = 60
        
        print(f"\n正在分析 {code}...")
        
        df = self.fetcher.get_historical_data(code, days=days)
        if df.empty:
            print("获取数据失败")
            return
        
        analyzer = TechnicalAnalyzer(df)
        signals = analyzer.get_latest_signals()
        
        print("\n技术指标分析结果:")
        print("="*40)
        print(f"MA5:  {signals.get('ma5', 'N/A'):.2f}" if isinstance(signals.get('ma5'), (int, float)) else f"MA5:  N/A")
        print(f"MA10: {signals.get('ma10', 'N/A'):.2f}" if isinstance(signals.get('ma10'), (int, float)) else f"MA10: N/A")
        print(f"MA20: {signals.get('ma20', 'N/A'):.2f}" if isinstance(signals.get('ma20'), (int, float)) else f"MA20: N/A")
        print(f"\nMACD: {signals.get('macd_signal', 'N/A')}")
        print(f"RSI:  {signals.get('rsi', 'N/A'):.2f} ({signals.get('rsi_signal', 'N/A')})")
        print(f"KDJ:  K={signals.get('k', 'N/A'):.2f}, D={signals.get('d', 'N/A'):.2f}, J={signals.get('j', 'N/A'):.2f}")
        print(f"信号: {signals.get('kdj_signal', 'N/A')}")
        print(f"\n趋势: {signals.get('trend', 'N/A')}")
    
    def plot_kline(self):
        """绘制K线图"""
        code = self.get_input("请输入股票代码: ")
        if not code:
            return
        
        days = self.get_input("分析天数 (默认90): ") or "90"
        indicators = self.get_input("显示指标 (ma,macd,rsi,boll, 默认全部): ") or "ma,macd,rsi,boll"
        
        try:
            days = int(days)
        except ValueError:
            days = 90
        
        print(f"\n正在获取 {code} 的数据...")
        df = self.fetcher.get_historical_data(code, days=days)
        
        if df.empty:
            print("获取数据失败")
            return
        
        indicator_list = [i.strip() for i in indicators.split(',') if i.strip()]
        
        print("正在绘制图表...")
        self.visualizer.plot_with_indicators(df, indicators=indicator_list, 
                                            title=f"{code} 技术分析")
    
    def stock_screening(self):
        """选股策略"""
        print("\n选股策略:")
        print("-" * 40)
        print("  1. MACD金叉策略")
        print("  2. RSI超卖策略")
        print("  3. 均线金叉策略")
        print("  4. 放量突破策略")
        print("  5. 多指标综合策略")
        print("  6. 基本面选股策略")
        print("-" * 40)
        
        choice = self.get_input("请选择策略 (1-6): ")
        
        # 获取股票列表
        print("\n正在获取股票列表...")
        all_stocks = self.fetcher.get_stock_list()
        
        if all_stocks.empty:
            print("获取股票列表失败")
            return
        
        # 限制分析数量以加快速度
        limit = self.get_input("分析股票数量 (默认100, 全部输入0): ") or "100"
        try:
            limit = int(limit)
            if limit > 0:
                stocks_to_analyze = all_stocks.head(limit)
            else:
                stocks_to_analyze = all_stocks
        except ValueError:
            stocks_to_analyze = all_stocks.head(100)
        
        print(f"\n开始分析 {len(stocks_to_analyze)} 只股票...")
        
        if choice == '1':
            strategy = MACDStrategy()
            results = strategy.filter(stocks_to_analyze)
            strategy_name = "MACD金叉"
        
        elif choice == '2':
            threshold = self.get_input("RSI阈值 (默认30): ") or "30"
            strategy = RSIStrategy(float(threshold))
            results = strategy.filter(stocks_to_analyze)
            strategy_name = "RSI超卖"
        
        elif choice == '3':
            short = self.get_input("短期均线 (默认5): ") or "5"
            long = self.get_input("长期均线 (默认20): ") or "20"
            strategy = GoldenCrossStrategy(int(short), int(long))
            results = strategy.filter(stocks_to_analyze)
            strategy_name = f"MA{short}金叉MA{long}"
        
        elif choice == '4':
            ratio = self.get_input("成交量放大倍数 (默认2.0): ") or "2.0"
            strategy = VolumeBreakoutStrategy(float(ratio))
            results = strategy.filter(stocks_to_analyze)
            strategy_name = "放量突破"
        
        elif choice == '5':
            strategy = MultiIndicatorStrategy()
            results = strategy.filter(stocks_to_analyze)
            strategy_name = "多指标综合"
        
        elif choice == '6':
            print("\n基本面筛选条件:")
            max_pe = self.get_input("最大市盈率 (默认30, 不限输入0): ") or "30"
            max_pe = float(max_pe) if max_pe != "0" else None
            
            max_pb = self.get_input("最大市净率 (默认3, 不限输入0): ") or "3"
            max_pb = float(max_pb) if max_pb != "0" else None
            
            min_cap = self.get_input("最小市值(亿元, 默认100, 不限输入0): ") or "100"
            min_cap = float(min_cap) if min_cap != "0" else None
            
            max_cap = self.get_input("最大市值(亿元, 默认不限): ") or None
            max_cap = float(max_cap) if max_cap else None
            
            strategy = FundamentalStrategy()
            results = strategy.filter(
                stocks_to_analyze,
                max_pe=max_pe,
                max_pb=max_pb,
                min_market_cap=min_cap,
                max_market_cap=max_cap
            )
            strategy_name = "基本面选股"
        
        else:
            print("无效选择")
            return
        
        print(f"\n{'='*50}")
        print(f"策略: {strategy_name}")
        print(f"符合条件股票数: {len(results)}")
        print(f"{'='*50}")
        
        if not results.empty:
            if 'score' in results.columns:
                print(results[['code', 'name', 'score', 'price']].head(20).to_string())
            else:
                print(results.head(20).to_string())
        else:
            print("未找到符合条件的股票")
    
    def sector_analysis(self):
        """行业板块分析"""
        print("\n正在获取行业板块数据...")
        sectors = self.fetcher.get_industry_ranking()
        
        if sectors.empty:
            print("获取失败")
            return
        
        print(f"\n行业板块涨跌排行:")
        print("="*60)
        print(f"{'行业':<15} {'涨跌幅':>10} {'领涨股':<15} {'领涨股涨幅':>10}")
        print("-"*60)
        
        for _, row in sectors.head(20).iterrows():
            print(f"{row.get('板块名称', 'N/A'):<15} {row.get('涨跌幅', 'N/A'):>10.2f}% "
                  f"{row.get('领涨股', 'N/A'):<15} {row.get('领涨股涨幅', 'N/A'):>10.2f}%")
    
    def concept_analysis(self):
        """概念板块分析"""
        concept = self.get_input("请输入概念名称 (如: 人工智能, 芯片, 新能源车): ")
        if not concept:
            print("概念名称不能为空")
            return
        
        print(f"\n正在获取 {concept} 板块数据...")
        stocks = self.fetcher.get_concept_stocks(concept)
        
        if stocks.empty:
            print("获取失败，可能该概念不存在")
            return
        
        print(f"\n{concept} 板块包含 {len(stocks)} 只股票:")
        print(stocks.head(30).to_string())
    
    def run(self):
        """运行主循环"""
        print("\n欢迎使用A股分析系统!")
        print("提示: 股票代码格式 - 平安银行: 000001, 浦发银行: 600000")
        
        while self.running:
            self.print_menu()
            choice = self.get_input("请选择功能 (0-7): ")
            
            try:
                if choice == '0':
                    self.running = False
                    print("感谢使用，再见!")
                
                elif choice == '1':
                    self.show_stock_list()
                
                elif choice == '2':
                    self.query_single_stock()
                
                elif choice == '3':
                    self.technical_analysis()
                
                elif choice == '4':
                    self.plot_kline()
                
                elif choice == '5':
                    self.stock_screening()
                
                elif choice == '6':
                    self.sector_analysis()
                
                elif choice == '7':
                    self.concept_analysis()
                
                else:
                    print("无效选择，请重新输入")
            
            except KeyboardInterrupt:
                print("\n\n操作已取消")
            except Exception as e:
                print(f"\n发生错误: {str(e)}")
                print("请检查输入或网络连接")


def quick_analysis(code: str, days: int = 60):
    """
    快速分析单只股票
    
    Args:
        code: 股票代码
        days: 分析天数
    """
    print(f"\n{'='*50}")
    print(f"快速分析: {code}")
    print(f"{'='*50}")
    
    fetcher = StockDataFetcher()
    
    # 获取数据
    df = fetcher.get_historical_data(code, days=days)
    if df.empty:
        print("获取数据失败")
        return
    
    # 技术分析
    analyzer = TechnicalAnalyzer(df)
    signals = analyzer.get_latest_signals()
    
    # 显示结果
    print("\n最新行情:")
    print(f"  收盘价: {df['close'].iloc[-1]:.2f}")
    print(f"  涨跌幅: {df['pct_change'].iloc[-1]:.2f}%")
    print(f"  成交量: {df['volume'].iloc[-1]:,.0f}")
    
    print("\n技术指标:")
    print(f"  MA5:  {signals.get('ma5', 'N/A'):.2f}")
    print(f"  MA20: {signals.get('ma20', 'N/A'):.2f}")
    print(f"  MACD: {signals.get('macd_signal', 'N/A')}")
    print(f"  RSI:  {signals.get('rsi', 'N/A'):.2f}")
    print(f"  KDJ:  K={signals.get('k', 'N/A'):.2f} D={signals.get('d', 'N/A'):.2f} J={signals.get('j', 'N/A'):.2f}")
    print(f"  趋势: {signals.get('trend', 'N/A')}")
    
    # 绘制图表
    print("\n正在绘制技术分析图...")
    visualizer = StockVisualizer()
    visualizer.plot_with_indicators(df, title=f"{code} 技术分析")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='A股分析系统')
    parser.add_argument('--code', '-c', type=str, help='股票代码，快速分析模式')
    parser.add_argument('--days', '-d', type=int, default=60, help='分析天数')
    
    args = parser.parse_args()
    
    if args.code:
        # 快速分析模式
        quick_analysis(args.code, args.days)
    else:
        # 交互式模式
        cli = StockAnalyzerCLI()
        cli.run()


if __name__ == "__main__":
    main()