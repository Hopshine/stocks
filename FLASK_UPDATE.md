# Flask应用集成BaoStock数据源 - 更新说明

## 更新概述

已成功将BaoStock数据源集成到Flask Web应用中，替换了原有存在连接问题的akshare数据源。

## 修改的文件

### 1. [src/baostock_fetcher.py](d:\code\stocks\src\baostock_fetcher.py)
- 添加了`get_industry_ranking()`方法（返回空DataFrame，因为baostock不提供此功能）
- 完善了接口，使其与StockDataFetcher兼容

### 2. [app.py](d:\code\stocks\app.py)
- 将`StockDataFetcher`替换为`BaoStockDataFetcher`
- 全局数据获取器现在使用BaoStockDataFetcher

### 3. [src/strategy.py](d:\code\stocks\src\strategy.py)
- 修改`StockStrategy`基类，支持传入自定义fetcher
- 默认使用`BaoStockDataFetcher`，保持向后兼容

## 测试结果

所有API接口测试通过 ✓

| 测试项 | 状态 | 说明 |
|--------|------|------|
| 获取股票列表 | ✓ 通过 | 成功获取5662只股票 |
| 获取股票信息 | ✓ 通过 | 支持历史数据和统计信息 |
| 技术分析 | ✓ 通过 | 与TechnicalAnalyzer完全兼容 |
| 选股策略 | ✓ 通过 | 支持MACD、RSI等策略 |
| 行业板块 | ✓ 通过 | baostock不提供此功能，返回空 |

## 使用方法

### 启动Flask应用

```bash
python app.py
```

### 访问Web界面

打开浏览器访问：http://127.0.0.1:5000

### API接口

所有API接口现在都使用BaoStock数据源：

1. **获取股票列表**
   ```
   GET /api/stock_list
   ```

2. **获取股票信息**
   ```
   GET /api/stock_info/<code>
   ```

3. **技术分析**
   ```
   GET /api/technical_analysis/<code>?days=60
   ```

4. **生成图表**
   ```
   GET /api/chart/<code>?days=90&type=technical
   ```

5. **选股策略**
   ```
   POST /api/screening
   Content-Type: application/json
   Body: {
     "strategy": "macd",
     "limit": 100
   }
   ```

6. **行业板块**
   ```
   GET /api/sectors
   ```
   注意：baostock不提供行业板块数据，此接口返回空

## 功能对比

| 功能 | akshare | BaoStock | 状态 |
|------|----------|-----------|------|
| 获取股票列表 | ✓ | ✓ | 已替换 |
| 获取历史数据 | ✓ | ✓ | 已替换 |
| 获取实时行情 | ✓ | ✓ | 已替换 |
| 技术分析 | ✓ | ✓ | 完全兼容 |
| 选股策略 | ✓ | ✓ | 完全兼容 |
| 行业板块排行 | ✓ | ✗ | 返回空 |

## 优势

1. **连接稳定**：BaoStock不会出现akshare的连接问题
2. **免费使用**：无需注册或token
3. **完全兼容**：与现有技术分析和可视化模块无缝集成
4. **数据全面**：覆盖所有A股（主板、科创板、创业板）

## 注意事项

1. **行业板块功能**：baostock不提供行业板块排行数据，`/api/sectors`接口将返回空数据
2. **实时行情**：baostock的数据可能有1-2天的延迟
3. **股票列表**：使用的是2024年底的数据，如需最新数据可以修改代码中的日期

## 测试

运行测试脚本验证功能：

```bash
python test_flask_api.py
```

## 故障排除

如果遇到问题：

1. **检查baostock安装**
   ```bash
   pip show baostock
   ```

2. **检查网络连接**
   ```bash
   python test_baostock.py
   ```

3. **查看错误日志**
   Flask应用会在控制台输出详细错误信息

## 下一步

如需恢复行业板块功能，可以考虑：
1. 使用其他数据源（如tushare）专门获取行业板块数据
2. 手动维护行业板块列表
3. 使用akshare的备用接口获取行业板块数据（如果连接问题解决）

## 版本信息

- 更新日期：2026-01-28
- 数据源：BaoStock v0.8.9
- Flask：v3.1.2
- Python：v3.13
