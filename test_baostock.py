#!/usr/bin/env python3
"""
测试baostock连接
"""
import baostock as bs
import pandas as pd

def test_baostock():
    """测试baostock连接和基本功能"""
    print("=" * 60)
    print("测试baostock连接")
    print("=" * 60)
    
    # 登录系统
    lg = bs.login()
    if lg.error_code != '0':
        print(f"❌ 登录失败: {lg.error_msg}")
        return False
    print("✓ 登录成功")
    
    # 获取股票列表
    print("\n测试1: 获取股票列表...")
    rs = bs.query_all_stock(day='2024-12-31')
    if rs.error_code != '0':
        print(f"❌ 获取股票列表失败: {rs.error_msg}")
        bs.logout()
        return False
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    result = pd.DataFrame(data_list, columns=rs.fields)
    print(f"✓ 成功获取 {len(result)} 只股票")
    print(f"  列名: {list(result.columns)}")
    print(f"  前5行:")
    print(result.head())
    
    # 获取单只股票历史数据
    print("\n测试2: 获取平安银行(000001)历史数据...")
    rs = bs.query_history_k_data_plus(
        "sz.000001",
        "date,code,open,high,low,close,volume,amount,pctChg",
        start_date='2024-01-01',
        end_date='2024-12-31',
        frequency="d",
        adjustflag="3"
    )
    
    if rs.error_code != '0':
        print(f"❌ 获取历史数据失败: {rs.error_msg}")
        bs.logout()
        return False
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    result = pd.DataFrame(data_list, columns=rs.fields)
    print(f"✓ 成功获取 {len(result)} 条历史数据")
    print(f"  列名: {list(result.columns)}")
    print(f"  最新5行:")
    print(result.tail())
    
    # 登出系统
    bs.logout()
    print("\n✓ 登出成功")
    
    return True

if __name__ == "__main__":
    success = test_baostock()
    if success:
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！baostock可以正常使用")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
