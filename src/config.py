"""
股票行情自动获取系统配置
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 数据库配置
DB_CONFIG = {
    'stock_cache': PROJECT_ROOT / 'data' / 'stock_cache.db',
    'sync_log': PROJECT_ROOT / 'logs' / 'sync.log',
    'error_log': PROJECT_ROOT / 'logs' / 'error.log',
}

# 调度配置
SCHEDULER_CONFIG = {
    # 股票列表更新间隔（小时）
    'stock_list_interval_hours': 24,
    # 实时行情更新间隔（分钟）
    'market_data_interval_minutes': 5,
    # 指数数据更新间隔（分钟）
    'index_data_interval_minutes': 5,
    # 是否启用自动更新
    'auto_start': True,
}

# API配置
API_CONFIG = {
    # baostock配置
    'baostock': {
        'enabled': True,
        'retry_times': 3,
        'retry_interval_seconds': 5,
    },
    # akshare配置（备用）
    'akshare': {
        'enabled': False,
        'retry_times': 3,
        'retry_interval_seconds': 10,
    },
}

# 股票配置
STOCK_CONFIG = {
    # 是否只获取A股
    'a_shares_only': True,
    # 关注的板块
    '关注的板块': ['银行', '证券', '保险', '白酒', '医药', '科技'],
    # 自选股列表（代码）
    'watchlist': [
        '600000', '600036', '601398',  # 银行
        '600030', '601066', '600999',  # 证券
        '601319', '601628', '601336',  # 保险
        '600519', '000858', '洋河股份',  # 白酒
        '600276', '000538', '600436',  # 医药
    ],
}

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'max_bytes': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
}

# 数据保留策略
DATA_RETENTION = {
    # 实时行情保留天数
    'market_data_days': 30,
    # 指数数据保留天数
    'index_data_days': 30,
    # 日志保留天数
    'log_days': 90,
}
