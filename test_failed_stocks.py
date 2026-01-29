from src.baostock_fetcher import BaoStockDataFetcher

fetcher = BaoStockDataFetcher()

# 测试几个失败的股票
failed_codes = ['600705', '000622', '000851', '600387', '300280']

print("测试失败的股票详情:")
for code in failed_codes:
    # 获取股票信息
    stocks = fetcher.get_stock_list()
    stock_info = stocks[stocks['code'] == code]
    
    if not stock_info.empty:
        print(f"\n{code} - {stock_info.iloc[0]['name']} (状态: {stock_info.iloc[0]['status']})")
        
        # 尝试获取历史数据
        hist = fetcher.get_historical_data(code, days=10)
        if not hist.empty:
            print(f"  历史数据: {len(hist)} 条")
            print(f"  最近日期: {hist.index[-1].strftime('%Y-%m-%d')}")
            print(f"  最近价格: {hist['close'].iloc[-1]:.2f}")
        else:
            print(f"  无历史数据")
    else:
        print(f"\n{code} - 未找到股票信息")
