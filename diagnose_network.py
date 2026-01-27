#!/usr/bin/env python3
"""
诊断网络连接问题
"""
import sys
import os
import requests
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_network_connectivity():
    """测试网络连接"""
    print("=" * 60)
    print("测试网络连接")
    print("=" * 60)
    
    test_urls = [
        ("百度", "https://www.baidu.com"),
        ("东方财富", "https://quote.eastmoney.com"),
        ("新浪财经", "https://finance.sina.com.cn"),
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for name, url in test_urls:
        try:
            print(f"\n测试连接到 {name} ({url})...")
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  ✓ 连接成功 - 状态码: {response.status_code}")
        except Exception as e:
            print(f"  ✗ 连接失败: {e}")

def test_akshare_api():
    """测试akshare API"""
    print("\n" + "=" * 60)
    print("测试akshare API")
    print("=" * 60)
    
    try:
        import akshare as ak
        print("✓ akshare模块导入成功")
        print(f"  版本: {ak.__version__}")
    except Exception as e:
        print(f"✗ akshare模块导入失败: {e}")
        return
    
    # 测试几个akshare函数
    test_functions = [
        ("获取上证指数", lambda: ak.index_zh_a_hist(symbol="000001", period="daily")),
        ("获取A股列表(上海)", lambda: ak.stock_sh_a_spot_em()),
    ]
    
    for name, func in test_functions:
        try:
            print(f"\n测试: {name}...")
            result = func()
            if hasattr(result, 'empty') and not result.empty:
                print(f"  ✓ 成功 - 返回 {len(result)} 条数据")
            elif hasattr(result, '__len__') and len(result) > 0:
                print(f"  ✓ 成功 - 返回数据")
            else:
                print(f"  ⚠ 返回空数据")
        except Exception as e:
            print(f"  ✗ 失败: {type(e).__name__}: {e}")

def test_proxy_settings():
    """测试代理设置"""
    print("\n" + "=" * 60)
    print("检查代理设置")
    print("=" * 60)
    
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                   'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
    
    has_proxy = False
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"  ⚠ 发现代理设置: {var}={value}")
            has_proxy = True
    
    if not has_proxy:
        print("  ✓ 未发现代理设置")

def main():
    """运行所有诊断"""
    print("\n" + "=" * 60)
    print("股票应用网络连接诊断")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    test_proxy_settings()
    test_network_connectivity()
    test_akshare_api()
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    print("\n建议:")
    print("1. 如果所有网络连接都失败，请检查网络连接")
    print("2. 如果akshare API失败但其他网站正常，可能是:")
    print("   - akshare服务器暂时不可用")
    print("   - IP被限制（可以尝试更换网络或等待一段时间）")
    print("   - akshare版本过旧（尝试升级: pip install akshare --upgrade）")
    print("3. 如果发现代理设置，可以尝试清除代理环境变量")

if __name__ == "__main__":
    main()
