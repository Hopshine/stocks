"""
SQLite缓存模块 - 用于缓存股票数据
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import os


class StockDataCache:
    """股票数据缓存类"""
    
    def __init__(self, db_path: str = "data/stock_cache.db"):
        """
        初始化缓存
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 股票列表缓存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    name TEXT,
                    status TEXT,
                    market TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 历史数据缓存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historical_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    amount REAL,
                    pct_change REAL,
                    turnover REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(code, date)
                )
            ''')
            
            # 实时行情缓存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spot_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    data TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 指数数据缓存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS index_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    amount REAL,
                    pct_change REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(code, date)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_list_code ON stock_list(code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_historical_code ON historical_data(code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_historical_date ON historical_data(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_historical_code_date ON historical_data(code, date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_spot_code ON spot_data(code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_index_code ON index_data(code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_index_date ON index_data(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_index_code_date ON index_data(code, date)')
            
            conn.commit()
    
    def get_stock_list(self, max_age_hours: int = 24) -> Optional[pd.DataFrame]:
        """
        获取缓存的股票列表
        
        Args:
            max_age_hours: 最大缓存时间（小时）
            
        Returns:
            DataFrame或None（如果缓存过期或不存在）
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查缓存是否存在且未过期
            cursor.execute('''
                SELECT COUNT(*) FROM stock_list
                WHERE updated_at > datetime('now', '-{} hours')
            '''.format(max_age_hours))
            
            count = cursor.fetchone()[0]
            
            if count == 0:
                return None
            
            # 获取缓存数据
            cursor.execute('''
                SELECT code, name, status, market 
                FROM stock_list
                WHERE updated_at > datetime('now', '-{} hours')
            '''.format(max_age_hours))
            
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            df = pd.DataFrame(rows, columns=['code', 'name', 'status', 'market'])
            return df
    
    def save_stock_list(self, df: pd.DataFrame):
        """
        保存股票列表到缓存
        
        Args:
            df: 股票列表DataFrame
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 清除旧数据
            cursor.execute('DELETE FROM stock_list')
            
            # 插入新数据
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT INTO stock_list (code, name, status, market)
                    VALUES (?, ?, ?, ?)
                ''', (row['code'], row['name'], row['status'], row['market']))
            
            conn.commit()
    
    def get_historical_data(
        self,
        code: str,
        start_date: str,
        end_date: str,
        max_age_hours: int = 1
    ) -> Optional[pd.DataFrame]:
        """
        获取缓存的历史数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            max_age_hours: 最大缓存时间（小时）
            
        Returns:
            DataFrame或None（如果缓存过期或不存在）
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查缓存是否存在且未过期
            cursor.execute('''
                SELECT COUNT(*) FROM historical_data
                WHERE code = ? AND updated_at > datetime('now', '-{} hours')
            '''.format(max_age_hours), (code,))
            
            count = cursor.fetchone()[0]
            
            if count == 0:
                return None
            
            # 获取缓存数据
            cursor.execute('''
                SELECT date, open, high, low, close, volume, amount, pct_change, turnover
                FROM historical_data
                WHERE code = ? AND date >= ? AND date <= ?
                ORDER BY date ASC
            ''', (code, start_date, end_date))
            
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            df = pd.DataFrame(rows, columns=[
                'date', 'open', 'high', 'low', 'close',
                'volume', 'amount', 'pct_change', 'turnover'
            ])
            
            # 转换数据类型
            df['date'] = pd.to_datetime(df['date'])
            for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change', 'turnover']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df.set_index('date', inplace=True)
            return df
    
    def save_historical_data(self, code: str, df: pd.DataFrame):
        """
        保存历史数据到缓存
        
        Args:
            code: 股票代码
            df: 历史数据DataFrame
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 删除该股票的旧数据
            cursor.execute('DELETE FROM historical_data WHERE code = ?', (code,))
            
            # 插入新数据
            for date, row in df.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO historical_data 
                    (code, date, open, high, low, close, volume, amount, pct_change, turnover)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    code,
                    date.strftime('%Y-%m-%d'),
                    row['open'], row['high'], row['low'], row['close'],
                    row['volume'], row['amount'], row['pct_change'], row['turnover']
                ))
            
            conn.commit()
    
    def get_spot_data(self, code: str, max_age_hours: int = 1) -> Optional[dict]:
        """
        获取缓存的实时行情
        
        Args:
            code: 股票代码
            max_age_hours: 最大缓存时间（小时）
            
        Returns:
            dict或None（如果缓存过期或不存在）
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT data FROM spot_data
                WHERE code = ? AND updated_at > datetime('now', '-{} hours')
            '''.format(max_age_hours), (code,))
            
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            import json
            return json.loads(row[0])
    
    def save_spot_data(self, code: str, data: dict):
        """
        保存实时行情到缓存
        
        Args:
            code: 股票代码
            data: 实时行情数据
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            import json
            cursor.execute('''
                INSERT OR REPLACE INTO spot_data (code, data)
                VALUES (?, ?)
            ''', (code, json.dumps(data)))
            
            conn.commit()
    
    def get_index_data(
        self,
        code: str,
        start_date: str,
        end_date: str,
        max_age_hours: int = 1
    ) -> Optional[pd.DataFrame]:
        """
        获取缓存的指数数据
        
        Args:
            code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            max_age_hours: 最大缓存时间（小时）
            
        Returns:
            DataFrame或None（如果缓存过期或不存在）
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查缓存是否存在且未过期
            cursor.execute('''
                SELECT COUNT(*) FROM index_data
                WHERE code = ? AND updated_at > datetime('now', '-{} hours')
            '''.format(max_age_hours), (code,))
            
            count = cursor.fetchone()[0]
            
            if count == 0:
                return None
            
            # 获取缓存数据
            cursor.execute('''
                SELECT date, open, high, low, close, volume, amount, pct_change
                FROM index_data
                WHERE code = ? AND date >= ? AND date <= ?
                ORDER BY date ASC
            ''', (code, start_date, end_date))
            
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            df = pd.DataFrame(rows, columns=[
                'date', 'open', 'high', 'low', 'close',
                'volume', 'amount', 'pct_change'
            ])
            
            # 转换数据类型
            df['date'] = pd.to_datetime(df['date'])
            for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df.set_index('date', inplace=True)
            return df
    
    def save_index_data(self, code: str, df: pd.DataFrame):
        """
        保存指数数据到缓存
        
        Args:
            code: 指数代码
            df: 指数数据DataFrame
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 删除该指数的旧数据
            cursor.execute('DELETE FROM index_data WHERE code = ?', (code,))
            
            # 插入新数据
            for date, row in df.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO index_data 
                    (code, date, open, high, low, close, volume, amount, pct_change)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    code,
                    date.strftime('%Y-%m-%d'),
                    row['open'], row['high'], row['low'], row['close'],
                    row['volume'], row['amount'], row['pct_change']
                ))
            
            conn.commit()
    
    def clear_cache(self, table: Optional[str] = None):
        """
        清除缓存
        
        Args:
            table: 表名（None表示清除所有）
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if table is None:
                # 清除所有表
                cursor.execute('DELETE FROM stock_list')
                cursor.execute('DELETE FROM historical_data')
                cursor.execute('DELETE FROM spot_data')
                cursor.execute('DELETE FROM index_data')
            elif table == 'stock_list':
                cursor.execute('DELETE FROM stock_list')
            elif table == 'historical_data':
                cursor.execute('DELETE FROM historical_data')
            elif table == 'spot_data':
                cursor.execute('DELETE FROM spot_data')
            elif table == 'index_data':
                cursor.execute('DELETE FROM index_data')
            
            conn.commit()
    
    def get_cache_info(self) -> dict:
        """
        获取缓存信息
        
        Returns:
            包含缓存统计信息的字典
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            info = {}
            
            # 股票列表
            cursor.execute('SELECT COUNT(*) FROM stock_list')
            info['stock_list_count'] = cursor.fetchone()[0]
            
            # 历史数据
            cursor.execute('SELECT COUNT(*), COUNT(DISTINCT code) FROM historical_data')
            row = cursor.fetchone()
            info['historical_data_count'] = row[0]
            info['historical_stocks_count'] = row[1]
            
            # 实时行情
            cursor.execute('SELECT COUNT(*) FROM spot_data')
            info['spot_data_count'] = cursor.fetchone()[0]
            
            # 指数数据
            cursor.execute('SELECT COUNT(*), COUNT(DISTINCT code) FROM index_data')
            row = cursor.fetchone()
            info['index_data_count'] = row[0]
            info['index_stocks_count'] = row[1]
            
            # 数据库大小
            info['db_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)
            
            return info
