import requests
import json

print('测试API返回数据...')
r = requests.get('http://127.0.0.1:5000/api/stock_list', timeout=30)
if r.status_code == 200:
    data = r.json()
    if data.get('success'):
        print('=== API返回数据 ===')
        print(f'总数: {data["total_count"]}')
        print(f'上涨: {data["up_count"]}')
        print(f'下跌: {data["down_count"]}')
        print(f'平盘: {data["flat_count"]}')
        print(f'平均涨跌幅: {data["avg_change_pct"]:.2f}%')
        print(f'显示股票数: {data["count"]}')
        
        # 验证数据一致性
        total = data['up_count'] + data['down_count'] + data['flat_count']
        print(f'\n验证: {data["up_count"]} + {data["down_count"]} + {data["flat_count"]} = {total}')
        print(f'匹配: {"✓ 是" if total == data["total_count"] else "✗ 否"}')
    else:
        print(f'API错误: {data.get("error")}')
else:
    print(f'HTTP错误: {r.status_code}')
