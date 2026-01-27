"""
股票数据获取模块 - 使用baostock获取A股数据（带缓存）
"""
import baostock as bs
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from .cache import StockDataCache


class BaoStockDataFetcher:
    """A股数据获取器 - 使用baostock（带缓存）"""
    
    def __init__(self, enable_cache: bool = True, cache_path: str = "data/stock_cache.db"):
        """
        初始化数据获取器
        
        Args:
            enable_cache: 是否启用缓存
            cache_path: 缓存数据库路径
        """
        self.enable_cache = enable_cache
        self.cache = StockDataCache(cache_path) if enable_cache else None
        self.lg = None
        self._login()
    
    def _login(self):
        """登录baostock"""
        self.lg = bs.login()
        if self.lg.error_code != '0':
            print(f"登录baostock失败: {self.lg.error_msg}")
            raise Exception(f"登录失败: {self.lg.error_msg}")
    
    def _logout(self):
        """登出baostock"""
        if self.lg:
            bs.logout()
            self.lg = None
    
    def __del__(self):
        """析构时自动登出"""
        self._logout()
    
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取A股所有股票列表（带缓存）
        
        Returns:
            DataFrame包含: code, name等信息
        """
        try:
            # 尝试从缓存获取
            if self.enable_cache and self.cache:
                cached_data = self.cache.get_stock_list(max_age_hours=24)
                if cached_data is not None:
                    print(f"从缓存获取股票列表，共 {len(cached_data)} 只股票")
                    return cached_data
            
            # 尝试获取股票列表，从今天开始往前找最近的交易日
            dates_to_try = []
            
            # 添加今天和最近30天的工作日
            for i in range(30):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                dates_to_try.append(date)
            
            for date in dates_to_try:
                rs = bs.query_all_stock(day=date)
                
                if rs.error_code != '0':
                    continue
                
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                result = pd.DataFrame(data_list, columns=rs.fields)
                
                # 过滤出A股股票（排除指数）
                # 上海: 6开头主板, 0开头科创板
                # 深圳: 0开头主板, 3开头创业板
                a_stocks = result[
                    (result['code'].str.startswith('sh.6')) |  # 上海主板
                    (result['code'].str.startswith('sh.0')) |  # 上海科创板
                    (result['code'].str.startswith('sz.0')) |  # 深圳主板
                    (result['code'].str.startswith('sz.3'))    # 深圳创业板
                ].copy()
                
                # 如果没有A股股票，继续尝试下一个日期
                if len(a_stocks) == 0:
                    continue
                
                # 标准化列名
                a_stocks = a_stocks.rename(columns={
                    'code': 'code',
                    'code_name': 'name',
                    'tradeStatus': 'status'
                })
                
                # 添加市场标识
                a_stocks['market'] = a_stocks['code'].apply(
                    lambda x: 'SH' if x.startswith('sh.') else 'SZ'
                )
                
                # 去除代码前缀（sh./sz.）
                a_stocks['code'] = a_stocks['code'].str.replace(r'^(sh|sz)\.', '', regex=True)
                
                print(f"成功获取股票列表（日期: {date}），共 {len(a_stocks)} 只股票")
                
                # 保存到缓存
                if self.enable_cache and self.cache:
                    self.cache.save_stock_list(a_stocks)
                    print("已保存到缓存")
                
                return a_stocks[['code', 'name', 'status', 'market']]
            
            print("获取股票列表失败: 无法找到可用的交易日")
            return pd.DataFrame()
            
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_stock_spot(self, code: str) -> dict:
        """
        获取单只股票的实时行情（带缓存）
        
        Args:
            code: 股票代码 (如: 000001, 600000)
            
        Returns:
            包含实时行情数据的字典
        """
        try:
            # 尝试从缓存获取
            if self.enable_cache and self.cache:
                cached_data = self.cache.get_spot_data(code, max_age_hours=1)
                if cached_data is not None:
                    print(f"从缓存获取股票 {code} 实时行情")
                    return cached_data
            
            # 标准化代码格式
            if '.' not in code:
                if code.startswith('6'):
                    code = f'sh.{code}'
                else:
                    code = f'sz.{code}'
            
            # 获取最新一天的数据作为"实时"行情
            today = datetime.now().strftime('%Y-%m-%d')
            rs = bs.query_history_k_data_plus(
                code,
                "date,code,open,high,low,close,volume,amount,pctChg,turn",
                start_date=today,
                end_date=today,
                frequency="d",
                adjustflag="3"
            )
            
            if rs.error_code != '0':
                return {}
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return {}
            
            result = pd.DataFrame(data_list, columns=rs.fields)
            spot_data = result.iloc[0].to_dict()
            
            # 保存到缓存
            if self.enable_cache and self.cache:
                self.cache.save_spot_data(code, spot_data)
                print(f"已保存股票 {code} 实时行情到缓存")
            
            return spot_data
            
        except Exception as e:
            print(f"获取股票 {code} 实时行情失败: {e}")
            return {}
    
    def get_historical_data(
        self,
        code: str,
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        days: Optional[int] = None
    ) -> pd.DataFrame:
        """
        获取股票历史K线数据（带缓存）
        
        Args:
            code: 股票代码
            period: 周期 (daily/weekly/monthly)
            start_date: 开始日期 (YYYY-MM-DD格式), 默认为一年前
            end_date: 结束日期 (YYYY-MM-DD格式), 默认为今天
            adjust: 复权类型 (qfq-前复权, hfq-后复权, 不复权)
            days: 获取天数（如果指定，将覆盖start_date）
            
        Returns:
            DataFrame包含OHLCV数据
        """
        try:
            # 如果指定了days，计算start_date
            if days is not None:
                start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            # 标准化代码格式
            if '.' not in code:
                if code.startswith('6'):
                    code = f'sh.{code}'
                else:
                    code = f'sz.{code}'
            
            # 设置默认日期
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            # 尝试从缓存获取
            if self.enable_cache and self.cache:
                cached_data = self.cache.get_historical_data(
                    code, start_date, end_date, max_age_hours=1
                )
                if cached_data is not None:
                    print(f"从缓存获取股票 {code} 历史数据，共 {len(cached_data)} 条")
                    return cached_data
            
            # 设置复权标志
            adjustflag_map = {
                'qfq': '3',  # 前复权
                'hfq': '2',  # 后复权
                '': '1'      # 不复权
            }
            adjustflag = adjustflag_map.get(adjust, '3')
            
            # 设置频率
            frequency_map = {
                'daily': 'd',
                'weekly': 'w',
                'monthly': 'm'
            }
            frequency = frequency_map.get(period, 'd')
            
            # 获取数据
            rs = bs.query_history_k_data_plus(
                code,
                "date,code,open,high,low,close,volume,amount,pctChg,turn",
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjustflag=adjustflag
            )
            
            if rs.error_code != '0':
                print(f"获取股票 {code} 历史数据失败: {rs.error_msg}")
                return pd.DataFrame()
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return pd.DataFrame()
            
            result = pd.DataFrame(data_list, columns=rs.fields)
            
            # 标准化列名
            result.columns = [
                'date', 'code', 'open', 'high', 'low', 'close',
                'volume', 'amount', 'pct_change', 'turnover'
            ]
            
            # 转换数据类型
            result['date'] = pd.to_datetime(result['date'])
            for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change', 'turnover']:
                result[col] = pd.to_numeric(result[col], errors='coerce')
            
            result.set_index('date', inplace=True)
            
            # 保存到缓存
            if self.enable_cache and self.cache:
                self.cache.save_historical_data(code, result)
                print(f"已保存股票 {code} 历史数据到缓存，共 {len(result)} 条")
            
            return result
            
        except Exception as e:
            print(f"获取股票 {code} 历史数据失败: {e}")
            return pd.DataFrame()
    
    def get_index_data(self, index_code: str = "000001") -> pd.DataFrame:
        """
        获取指数数据（带缓存）
        
        Args:
            index_code: 指数代码 (000001-上证指数, 399001-深证成指, 399006-创业板指)
            
        Returns:
            DataFrame包含指数历史数据
        """
        try:
            # 标准化代码格式
            if '.' not in index_code:
                if index_code.startswith('000'):
                    index_code = f'sh.{index_code}'
                else:
                    index_code = f'sz.{index_code}'
            
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            # 尝试从缓存获取
            if self.enable_cache and self.cache:
                cached_data = self.cache.get_index_data(
                    index_code, start_date, end_date, max_age_hours=1
                )
                if cached_data is not None:
                    print(f"从缓存获取指数 {index_code} 数据，共 {len(cached_data)} 条")
                    return cached_data
            
            rs = bs.query_history_k_data_plus(
                index_code,
                "date,code,open,high,low,close,volume,amount,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="3"
            )
            
            if rs.error_code != '0':
                print(f"获取指数 {index_code} 数据失败: {rs.error_msg}")
                return pd.DataFrame()
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return pd.DataFrame()
            
            result = pd.DataFrame(data_list, columns=rs.fields)
            
            # 标准化列名
            result.columns = [
                'date', 'code', 'open', 'high', 'low', 'close',
                'volume', 'amount', 'pct_change'
            ]
            
            result['date'] = pd.to_datetime(result['date'])
            for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change']:
                result[col] = pd.to_numeric(result[col], errors='coerce')
            
            result.set_index('date', inplace=True)
            
            # 保存到缓存
            if self.enable_cache and self.cache:
                self.cache.save_index_data(index_code, result)
                print(f"已保存指数 {index_code} 数据到缓存，共 {len(result)} 条")
            
            return result
            
        except Exception as e:
            print(f"获取指数 {index_code} 数据失败: {e}")
            return pd.DataFrame()
    
    def get_industry_ranking(self, sort_by: str = "change_pct") -> pd.DataFrame:
        """
        获取行业板块涨跌幅排行
        
        注意: baostock不提供行业板块排行数据，此方法返回空DataFrame
        
        Args:
            sort_by: 排序字段
            
        Returns:
            DataFrame包含各行业板块数据（当前为空）
        """
        print("注意: baostock不提供行业板块排行数据")
        return pd.DataFrame(columns=['板块名称', '涨跌幅', '领涨股', '领涨股涨幅'])
    
    def clear_cache(self, table: Optional[str] = None):
        """
        清除缓存
        
        Args:
            table: 表名（None表示清除所有）
        """
        if self.cache:
            self.cache.clear_cache(table)
            print(f"已清除缓存: {table if table else '所有'}")
    
    def get_cache_info(self) -> dict:
        """
        获取缓存信息
        
        Returns:
            包含缓存统计信息的字典
        """
        if self.cache:
            return self.cache.get_cache_info()
        return {}


# 便捷函数
def fetch_stock_data(code: str, days: int = 365) -> pd.DataFrame:
    """
    快速获取股票历史数据的便捷函数
    
    Args:
        code: 股票代码
        days: 获取天数
        
    Returns:
        DataFrame
    """
    fetcher = BaoStockDataFetcher()
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return fetcher.get_historical_data(code, start_date=start_date)


def fetch_market_data() -> pd.DataFrame:
    """
    获取全市场股票数据
    
    Returns:
        DataFrame包含所有A股数据
    """
    fetcher = BaoStockDataFetcher()
    return fetcher.get_stock_list()
