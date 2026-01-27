#!/usr/bin/env python3
"""
测试baostock_fetcher - 调试版本
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import BaoStockDataFetcher

def test_stock_list_debug():
    """调试股票列表获取"""
    print("=" * 60)
    print("调试: 获取股票列表")
    print("=" * 60)
    
    fetcher = BaoStockDataFetcher()
    
    # 尝试使用不同的日期
    test_dates = [
        "2024-12-31",
        "2024-12-30",
        "2024-12-27",
        "2024-12-20"
    ]
    
    for date in test_dates:
        print(f"\n尝试日期: {date}")
        try:
            import baostock as bs
            rs = bs.query_all_stock(day=date)
            
            if rs.error_code != '0':
                print(f"  ✗ 失败: {rs.error_msg}")
                continue
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            result = pd.DataFrame(data_list, columns=rs.fields)
            print(f"  ✓ 成功获取 {len(result)} 条记录")
            
            # 检查数据内容
            print(f"  前5行:")
            print(result.head())
            
            # 过滤A股
            a_stocks = result[
                (result['code'].str.startswith('sh.6')) |
                (result['code'].str.startswith('sh.0')) |
                (result['code'].str.startswith('sz.0')) |
                (result['code'].str.startswith('sz.3'))
            ]
            print(f"  过滤后A股数量: {len(a_stocks)}")
            
            if len(a_stocks) > 0:
                print(f"\n✓ 找到可用的日期: {date}")
                return True
            
        except Exception as e:
            print(f"  ✗ 异常: {e}")
    
    return False

if __name__ == "__main__":
    import pandas as pd
    success = test_stock_list_debug()
    if success:
        print("\n✓ 测试成功")
    else:
        print("\n❌ 测试失败")
