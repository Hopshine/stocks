"""
A股分析系统 - 提供股票数据分析、技术指标计算和选股策略

主要功能:
- 股票数据获取 (akshare, baostock)
- 技术指标计算 (MA, MACD, RSI, KDJ, BOLL等)
- 选股策略 (MACD金叉、RSI超卖、均线金叉、放量突破等)
- 数据可视化 (K线图、技术分析图、收益对比等)
- 数据自动同步 (后台定时更新股票行情数据)

使用示例:
    >>> from src import BaoStockDataFetcher, TechnicalAnalyzer, StockVisualizer
    >>> fetcher = BaoStockDataFetcher()
    >>> df = fetcher.get_historical_data('000001')
    >>> analyzer = TechnicalAnalyzer(df)
    >>> signals = analyzer.get_latest_signals()
    
    # 后台调度器
    >>> from src import get_scheduler
    >>> scheduler = get_scheduler(auto_start=True)  # 启动后台同步
"""

from .data_fetcher import (
    StockDataFetcher,
    fetch_stock_data,
    fetch_market_data
)

from .baostock_fetcher import (
    BaoStockDataFetcher
)

from .cache import (
    StockDataCache
)

from .config import (
    DB_CONFIG,
    SCHEDULER_CONFIG,
    API_CONFIG,
    STOCK_CONFIG,
    LOG_CONFIG,
    DATA_RETENTION
)

from .data_sync import (
    DataSyncService,
    SyncLogger
)

from .scheduler import (
    StockScheduler,
    get_scheduler,
    start_scheduler,
    stop_scheduler
)

from .technical_analysis import (
    TechnicalAnalyzer,
    analyze_stock,
    calculate_all_indicators
)

from .visualization import (
    StockVisualizer,
    plot_stock_analysis,
    compare_stocks
)

from .strategy import (
    MACDStrategy,
    RSIStrategy,
    BollingerStrategy,
    GoldenCrossStrategy,
    VolumeBreakoutStrategy,
    MultiIndicatorStrategy,
    FundamentalStrategy,
    CompositeStrategy,
    find_macd_golden_cross,
    find_rsi_oversold,
    find_golden_cross,
    find_volume_breakout,
    multi_screening
)

__version__ = "1.1.0"
__author__ = "Stock Analyzer"

__all__ = [
    # 数据获取
    'StockDataFetcher',
    'BaoStockDataFetcher',
    'StockDataCache',
    'fetch_stock_data',
    'fetch_market_data',
    
    # 配置
    'DB_CONFIG',
    'SCHEDULER_CONFIG',
    'API_CONFIG',
    'STOCK_CONFIG',
    'LOG_CONFIG',
    'DATA_RETENTION',
    
    # 数据同步
    'DataSyncService',
    'SyncLogger',
    
    # 调度器
    'StockScheduler',
    'get_scheduler',
    'start_scheduler',
    'stop_scheduler',
    
    # 技术分析
    'TechnicalAnalyzer',
    'analyze_stock',
    'calculate_all_indicators',
    
    # 可视化
    'StockVisualizer',
    'plot_stock_analysis',
    'compare_stocks',
    
    # 策略
    'MACDStrategy',
    'RSIStrategy',
    'BollingerStrategy',
    'GoldenCrossStrategy',
    'VolumeBreakoutStrategy',
    'MultiIndicatorStrategy',
    'FundamentalStrategy',
    'CompositeStrategy',
    'find_macd_golden_cross',
    'find_rsi_oversold',
    'find_golden_cross',
    'find_volume_breakout',
    'multi_screening'
]