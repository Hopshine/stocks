# A股分析系统

一个功能全面的A股股票分析工具，提供数据获取、技术指标计算、选股策略和数据可视化功能。

## 功能特点

- **股票数据获取**: 使用akshare库实时获取A股数据
- **技术指标分析**: 支持MA、MACD、RSI、KDJ、BOLL等多种指标
- **选股策略**: 提供MACD金叉、RSI超卖、均线金叉、放量突破、多指标综合等策略
- **数据可视化**: 绘制K线图、技术指标图、收益对比图、相关性热力图等
- **交互式界面**: 提供命令行交互界面和快速分析模式

## 安装

### 1. 克隆或下载项目

```bash
cd d:\code\stocks
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

**注意**: TA-Lib 可能需要额外安装，如果安装失败可以先注释掉。

## 快速开始

### 方法一：Web界面 (推荐)

```bash
# 安装依赖
pip install -r requirements.txt

# 启动Web服务器
python app.py
```

然后打开浏览器访问: `http://127.0.0.1:5000`

### 方法二：交互式命令行界面

```bash
python main.py
```

### 方法三：快速分析模式

```bash
python main.py -c 000001 -d 60
```

分析平安银行(000001)近60天的数据。

## 功能模块

### Web界面功能

1. **首页** - 查看全市场股票涨跌幅排行和统计
2. **技术分析** - 对指定股票进行技术指标分析，生成图表
3. **智能选股** - 使用多种策略筛选股票
4. **行业板块** - 查看各行业板块涨跌情况
5. **股票对比** - 比较多只股票的表现

### 命令行界面功能

1. **查看股票列表** - 查看全市场股票涨跌幅排行
2. **查询单只股票行情** - 查询指定股票的实时和历史行情
3. **股票技术分析** - 对指定股票进行技术指标分析
4. **绘制K线图** - 绘制股票的K线图和技术指标图
5. **选股策略** - 使用各种策略筛选股票
6. **行业板块分析** - 查看各行业板块涨跌情况
7. **概念板块分析** - 查看指定概念板块的股票

## 使用示例

### 示例1: 获取股票数据

```python
from src import StockDataFetcher

fetcher = StockDataFetcher()

# 获取单只股票历史数据
df = fetcher.get_historical_data('000001', days=60)

# 获取实时行情
spot = fetcher.get_stock_spot('000001')

# 获取全市场数据
market = fetcher.get_stock_list()
```

### 示例2: 技术分析

```python
from src import TechnicalAnalyzer, fetch_stock_data

# 获取数据
df = fetch_stock_data('000001', days=60)

# 创建分析器
analyzer = TechnicalAnalyzer(df)

# 获取最新技术指标
signals = analyzer.get_latest_signals()
print(f"MA5: {signals['ma5']}")
print(f"RSI: {signals['rsi']}")
print(f"MACD: {signals['macd_signal']}")

# 计算所有指标
all_indicators = analyzer.generate_signals()
```

### 示例3: 选股策略

```python
from src import MACDStrategy, RSIStrategy, GoldenCrossStrategy
from src import StockDataFetcher

# 获取股票列表
fetcher = StockDataFetcher()
stocks = fetcher.get_stock_list()

# MACD金叉策略
strategy = MACDStrategy()
macd_results = strategy.filter(stocks.head(100))

# RSI超卖策略
rsi_strategy = RSIStrategy(oversold_threshold=30)
rsi_results = rsi_strategy.filter(stocks.head(100))

# 均线金叉策略
golden_cross = GoldenCrossStrategy(short_ma=5, long_ma=20)
cross_results = golden_cross.filter(stocks.head(100))
```

### 示例4: 数据可视化

```python
from src import StockVisualizer, fetch_stock_data

# 获取数据
df = fetch_stock_data('000001', days=90)

# 创建可视化器
visualizer = StockVisualizer()

# 绘制K线图
visualizer.plot_kline(df, title="平安银行 - K线图")

# 绘制技术指标图
visualizer.plot_with_indicators(
    df, 
    indicators=['ma', 'macd', 'rsi', 'boll'],
    title="平安银行 - 技术分析"
)
```

### 示例5: 多指标综合分析

```python
from src import MultiIndicatorStrategy, StockDataFetcher

fetcher = StockDataFetcher()
stocks = fetcher.get_stock_list()

# 多指标综合策略
strategy = MultiIndicatorStrategy()
results = strategy.filter(stocks.head(200))

# 按综合评分排序
print(results[['code', 'name', 'score', 'macd', 'rsi', 'boll']].head(20))
```

## 技术指标说明

| 指标 | 说明 | 信号 |
|------|------|------|
| MA | 移动平均线 | 多头排列/空头排列 |
| MACD | 指数平滑异同平均线 | 金叉/死叉 |
| RSI | 相对强弱指标 | 超买(>70)/超卖(<30) |
| KDJ | 随机指标 | 金叉/死叉 |
| BOLL | 布林带 | 触及上轨/下轨 |

## 选股策略说明

### MACD金叉策略
- 条件：MACD线上穿Signal线
- 说明：短期动能增强，买入信号

### RSI超卖策略
- 条件：RSI < 阈值（默认30）
- 说明：超卖状态，可能存在反弹机会

### 均线金叉策略
- 条件：短期均线上穿长期均线
- 说明：趋势转多

### 放量突破策略
- 条件：成交量放大倍数 > 2.0，且涨幅 > 3%
- 说明：资金流入明显

### 多指标综合策略
- 条件：MACD、RSI、BOLL、成交量、均线综合评分 >= 60分
- 说明：多个指标共振，信号更可靠

### 基本面选股策略
- 条件：PE < 30，PB < 3，市值 > 100亿
- 说明：价值投资筛选

## 项目结构

```
stocks/
├── src/
│   ├── __init__.py           # 模块初始化
│   ├── data_fetcher.py       # 数据获取模块
│   ├── technical_analysis.py # 技术分析模块
│   ├── strategy.py           # 选股策略模块
│   └── visualization.py      # 可视化模块
├── templates/                 # Web模板
│   ├── base.html             # 基础模板
│   ├── index.html            # 首页
│   ├── analysis.html         # 技术分析
│   ├── screening.html        # 选股策略
│   ├── stock_detail.html     # 股票详情
│   ├── sectors.html          # 行业板块
│   └── compare.html          # 股票对比
├── app.py                     # Flask Web应用
├── main.py                    # 命令行主程序
├── requirements.txt           # 依赖包列表
├── examples/
│   └── basic_usage.py         # 使用示例
└── README.md                  # 说明文档
```

## 数据来源

本项目使用[akshare](https://github.com/akfamily/akshare)获取A股数据，数据来自东方财富网、新浪财经等公开数据源。

## 注意事项

1. **网络连接**: 需要联网才能获取实时数据
2. **数据延迟**: 部分数据可能有延迟
3. **风险提示**: 本工具仅供学习研究，不构成投资建议
4. **交易时间**: 交易时间内数据更实时

## 扩展功能

### 添加自定义策略

```python
from src.strategy import StockStrategy

class MyStrategy(StockStrategy):
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        # 实现你的筛选逻辑
        return filtered_stocks
```

### 添加自定义指标

```python
from src.technical_analysis import TechnicalAnalyzer

class MyAnalyzer(TechnicalAnalyzer):
    def my_indicator(self, period: int = 20):
        # 实现你的指标计算
        return result
```

## 更新日志

### v1.0.0
- 实现基础数据获取功能
- 实现常见技术指标计算
- 实现多种选股策略
- 实现数据可视化功能
- 提供交互式命令行界面

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，欢迎反馈。

​

	

https://mirrors.aliyun.com/pypi/simple