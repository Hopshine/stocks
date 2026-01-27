# BaoStock数据源使用说明

## 简介

由于akshare数据源存在连接问题，项目已添加baostock作为备选数据源。baostock是一个免费、无需token的A股数据接口，非常适合获取国内A股数据。

## 安装

```bash
pip install baostock
```

## 基本使用

### 1. 导入模块

```python
from src import BaoStockDataFetcher
```

### 2. 创建数据获取器

```python
fetcher = BaoStockDataFetcher()
```

### 3. 获取股票列表

```python
# 获取所有A股股票列表
stocks = fetcher.get_stock_list()
print(f"共获取 {len(stocks)} 只股票")
print(stocks.head())
```

返回的DataFrame包含以下列：
- `code`: 股票代码（如：000001）
- `name`: 股票名称
- `status`: 交易状态
- `market`: 市场标识（SH-上海，SZ-深圳）

### 4. 获取历史数据

```python
# 获取平安银行最近60天的历史数据
df = fetcher.get_historical_data("000001", days=60)

# 或者指定日期范围
df = fetcher.get_historical_data(
    code="000001",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

返回的DataFrame包含以下列：
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量
- `amount`: 成交额
- `pct_change`: 涨跌幅
- `turnover`: 换手率

### 5. 获取实时行情

```python
# 获取单只股票的实时行情
spot = fetcher.get_stock_spot("000001")
print(spot)
```

### 6. 获取指数数据

```python
# 获取上证指数数据
index_df = fetcher.get_index_data("000001")

# 获取深证成指
index_df = fetcher.get_index_data("399001")

# 获取创业板指
index_df = fetcher.get_index_data("399006")
```

## 与现有模块的兼容性

BaoStockDataFetcher与现有的TechnicalAnalyzer、StockVisualizer等模块完全兼容：

```python
from src import BaoStockDataFetcher, TechnicalAnalyzer, StockVisualizer

# 获取数据
fetcher = BaoStockDataFetcher()
df = fetcher.get_historical_data("000001", days=60)

# 技术分析
analyzer = TechnicalAnalyzer(df)
signals = analyzer.get_latest_signals()
print(signals)

# 可视化
visualizer = StockVisualizer()
visualizer.plot_with_indicators(df, title="平安银行技术分析")
```

## 完整示例

```python
from src import BaoStockDataFetcher, TechnicalAnalyzer

# 创建数据获取器
fetcher = BaoStockDataFetcher()

# 获取股票列表
stocks = fetcher.get_stock_list()
print(f"共 {len(stocks)} 只股票")

# 获取历史数据
df = fetcher.get_historical_data("000001", days=60)
print(f"获取 {len(df)} 条历史数据")

# 技术分析
analyzer = TechnicalAnalyzer(df)
signals = analyzer.get_latest_signals()

print("\n技术指标:")
print(f"MA5:  {signals.get('ma5', 'N/A'):.2f}")
print(f"MA20: {signals.get('ma20', 'N/A'):.2f}")
print(f"MACD: {signals.get('macd', 'N/A'):.4f}")
print(f"RSI:  {signals.get('rsi', 'N/A'):.2f}")
print(f"趋势: {signals.get('trend', 'N/A')}")
```

## 优势

1. **免费使用**：无需注册或获取token
2. **数据全面**：覆盖所有A股（主板、科创板、创业板）
3. **稳定可靠**：官方维护，连接稳定
4. **易于使用**：API简单直观
5. **完全兼容**：与现有技术分析和可视化模块无缝集成

## 注意事项

1. BaoStock的数据可能不是实时数据，有1-2天的延迟
2. 股票列表使用的是2024年底的数据，如需最新数据可以修改日期
3. 每次创建BaoStockDataFetcher实例时会自动登录，使用完毕后会自动登出
4. 建议复用同一个fetcher实例，避免频繁登录登出

## 与akshare的对比

| 特性 | BaoStock | akshare |
|------|----------|---------|
| 是否需要token | 否 | 否 |
| 连接稳定性 | 高 | 中等 |
| 数据实时性 | 1-2天延迟 | 较实时 |
| 数据范围 | A股 | A股+港股+美股等 |
| 使用难度 | 简单 | 中等 |

## 运行示例

项目提供了完整的使用示例：

```bash
python examples/baostock_usage.py
```

该示例包含：
1. 获取股票列表
2. 获取历史数据
3. 技术分析
4. 多只股票对比
5. 简单选股

## 测试

运行测试脚本验证功能：

```bash
python test_baostock_integration.py
```

## 问题反馈

如遇到问题，请检查：
1. 是否正确安装了baostock：`pip show baostock`
2. 网络连接是否正常
3. 查看错误日志获取详细信息
