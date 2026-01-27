"""
测试代理修复是否成功
"""
import os
import sys

# 清除所有代理环境变量（在任何导入之前）
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
              'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
for var in proxy_vars:
    if var in os.environ:
        print(f"清除代理环境变量: {var}={os.environ[var]}")
        del os.environ[var]

# 现在导入akshare和data_fetcher
print("\n正在导入模块...")
try:
    from src.data_fetcher import StockDataFetcher
    print("✓ 模块导入成功")
except Exception as e:
    print(f"✗ 模块导入失败: {e}")
    sys.exit(1)

def test_stock_list():
    """测试获取股票列表"""
    print("\n" + "="*50)
    print("测试: 获取股票列表")
    print("="*50)
    
    fetcher = StockDataFetcher()
    
    print("正在获取股票列表...")
    df = fetcher.get_stock_list()
    
    if df.empty:
        print("✗ 获取股票列表失败 - 返回空数据")
        return False
    
    print(f"✓ 成功获取 {len(df)} 只股票")
    print(f"列名: {list(df.columns)}")
    print("\n前5条数据:")
    print(df.head().to_string())
    return True

def test_single_stock():
    """测试获取单只股票数据"""
    print("\n" + "="*50)
    print("测试: 获取单只股票实时行情 (000001)")
    print("="*50)
    
    fetcher = StockDataFetcher()
    
    try:
        data = fetcher.get_stock_spot("000001")
        if data:
            print(f"✓ 成功获取股票数据")
            print(f"数据项数: {len(data)}")
            return True
        else:
            print("✗ 获取股票数据失败 - 返回空数据")
            return False
    except Exception as e:
        print(f"✗ 获取股票数据失败: {e}")
        return False

def test_historical_data():
    """测试获取历史数据"""
    print("\n" + "="*50)
    print("测试: 获取历史数据 (000001, 最近5天)")
    print("="*50)
    
    fetcher = StockDataFetcher()
    
    try:
        df = fetcher.get_historical_data("000001", period="daily")
        if not df.empty:
            print(f"✓ 成功获取历史数据")
            print(f"数据条数: {len(df)}")
            print("\n最近5条数据:")
            print(df.tail().to_string())
            return True
        else:
            print("✗ 获取历史数据失败 - 返回空数据")
            return False
    except Exception as e:
        print(f"✗ 获取历史数据失败: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("代理修复测试脚本")
    print("="*50)
    
    # 显示当前环境
    print("\n当前工作目录:", os.getcwd())
    print("Python版本:", sys.version)
    
    # 运行测试
    results = []
    
    try:
        results.append(("股票列表", test_stock_list()))
    except Exception as e:
        print(f"\n✗ 股票列表测试异常: {e}")
        results.append(("股票列表", False))
    
    try:
        results.append(("单只股票", test_single_stock()))
    except Exception as e:
        print(f"\n✗ 单只股票测试异常: {e}")
        results.append(("单只股票", False))
    
    try:
        results.append(("历史数据", test_historical_data()))
    except Exception as e:
        print(f"\n✗ 历史数据测试异常: {e}")
        results.append(("历史数据", False))
    
    # 显示测试结果摘要
    print("\n" + "="*50)
    print("测试结果摘要")
    print("="*50)
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
    
    # 最终结论
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\n总计: {passed_count}/{total_count} 项测试通过")
    
    if passed_count == total_count:
        print("\n🎉 所有测试通过！代理修复成功！")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败，请检查网络连接或稍后再试")
        sys.exit(1)