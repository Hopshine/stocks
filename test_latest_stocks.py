#!/usr/bin/env python3
"""
测试获取最新股票列表
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import BaoStockDataFetcher

def test_latest_stock_list():
    """测试获取最新股票列表"""
    print("=" * 60)
    print("测试获取最新股票列表")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    stocks = fetcher.get_stock_list()
    
    if stocks.empty:
        print("❌ 获取股票列表失败")
        return False
    
    print(f"\n✓ 成功获取 {len(stocks)} 只股票")
    print(f"\n前10只股票:")
    print(stocks.head(10).to_string())
    
    # 统计各市场股票数量
    print(f"\n市场分布:")
    print(stocks['market'].value_counts())
    
    # 显示一些具体股票
    print(f"\n一些知名股票:")
    famous_stocks = ['000001', '000002', '600000', '600036', '600519']
    for code in famous_stocks:
        stock = stocks[stocks['code'] == code]
        if not stock.empty:
            print(f"  {code}: {stock.iloc[0]['name']}")
    
    return True

if __name__ == "__main__":
    success = test_latest_stock_list()
    if success:
        print("\n✓ 测试成功！现在使用的是最新股票列表")
    else:
        print("\n❌ 测试失败")
