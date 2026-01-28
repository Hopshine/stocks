"""
股票数据获取模块 - 使用baostock获取A股数据（带缓存）
"""
import baostock as bs
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from .cache import StockDataCache
from . import baostock_global


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
        """登录baostock（使用全局登录）"""
        try:
            self.lg = baostock_global.global_login()
        except Exception as e:
            print(f"登录baostock失败: {e}")
            raise
    
    def _logout(self):
        """登出baostock（使用全局登出）"""
        if self.lg:
            try:
                baostock_global.global_logout()
            except Exception:
                pass
            self.lg = None
    
    def __del__(self):
        """析构时自动登出（已禁用，避免影响其他实例）"""
        pass
    
    def close(self):
        """手动关闭连接"""
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
            
            # 尝试获取股票列表，使用多个日期策略
            dates_to_try = []
            
            # 策略1: 使用已知的历史交易日（baostock数据通常有延迟）
            # 使用2024年底和2025年初的日期
            known_trading_dates = [
                '2025-01-27', '2025-01-24', '2025-01-23', '2025-01-22', '2025-01-21',
                '2025-01-20', '2025-01-17', '2025-01-16', '2025-01-15', '2025-01-14',
                '2025-01-13', '2025-01-10', '2025-01-09', '2025-01-08', '2025-01-07',
                '2025-01-06', '2025-01-03', '2025-01-02', '2024-12-31', '2024-12-30',
                '2024-12-27', '2024-12-26', '2024-12-25', '2024-12-24', '2024-12-23'
            ]
            dates_to_try.extend(known_trading_dates)
            
            # 策略2: 从今天开始往前找最近的60天（作为后备）
            for i in range(60):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                if date not in dates_to_try:
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
                # 上海主板: sh.600000-604999
                # 上海科创板: sh.688000-688999
                # 深圳主板: sz.000xxx, sz.001xxx
                # 深圳创业板: sz.300xxx
                a_stocks = result[
                    (result['code'].str.startswith('sh.60')) |  # 上海主板
                    (result['code'].str.startswith('sh.688')) |  # 上海科创板
                    (result['code'].str.startswith('sz.000')) |  # 深圳主板
                    (result['code'].str.startswith('sz.001')) |  # 深圳主板
                    (result['code'].str.startswith('sz.300'))    # 深圳创业板
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
            
            # 获取最近一个交易日的数据作为"实时"行情
            # 从今天开始往前查找最近的交易日
            for i in range(30):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                rs = bs.query_history_k_data_plus(
                    code,
                    "date,code,open,high,low,close,volume,amount,pctChg,turn",
                    start_date=date,
                    end_date=date,
                    frequency="d",
                    adjustflag="3"
                )
                
                if rs.error_code != '0':
                    continue
                
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                if data_list:
                    result = pd.DataFrame(data_list, columns=rs.fields)
                    spot_data = result.iloc[0].to_dict()
                    
                    # 保存到缓存
                    if self.enable_cache and self.cache:
                        self.cache.save_spot_data(code, spot_data)
                        print(f"已保存股票 {code} 实时行情到缓存")
                    
                    return spot_data
            
            return {}
            
        except Exception as e:
            print(f"获取股票 {code} 实时行情失败: {e}")
            return {}
    
    def get_batch_spot_data(self, codes: list) -> dict:
        """
        批量获取多只股票的实时行情
        
        Args:
            codes: 股票代码列表 (如: ['000001', '600000'])
            
        Returns:
            字典，key为股票代码，value为行情数据
        """
        try:
            result = {}
            
            if not codes:
                return result
            
            # 步骤1: 批量获取缓存中有效的数据
            if self.enable_cache and self.cache:
                for code in codes:
                    cached_data = self.cache.get_spot_data(code, max_age_hours=1)
                    if cached_data is not None:
                        result[code] = cached_data
            
            # 步骤2: 找出需要从API获取的股票
            codes_need_fetch = [code for code in codes if code not in result]
            
            if not codes_need_fetch:
                print(f"所有 {len(codes)} 只股票的实时行情都来自缓存")
                return result
            
            print(f"需要从API获取 {len(codes_need_fetch)} 只股票的实时行情")
            
            # 步骤3: 从今天开始往前查找最近的交易日
            for i in range(30):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                
                # 如果所有需要获取的股票都有了数据，提前退出
                codes_remaining = [code for code in codes_need_fetch if code not in result]
                if not codes_remaining:
                    print(f"已获取所有股票的实时行情")
                    break
                
                for code in codes_remaining:
                    if code in result:
                        continue
                    
                    # 标准化代码格式
                    code_with_prefix = code
                    if '.' not in code:
                        if code.startswith('6'):
                            code_with_prefix = f'sh.{code}'
                        else:
                            code_with_prefix = f'sz.{code}'
                    
                    rs = bs.query_history_k_data_plus(
                        code_with_prefix,
                        "date,code,open,high,low,close,volume,amount,pctChg,turn",
                        start_date=date,
                        end_date=date,
                        frequency="d",
                        adjustflag="3"
                    )
                    
                    if rs.error_code != '0':
                        continue
                    
                    data_list = []
                    while (rs.error_code == '0') & rs.next():
                        data_list.append(rs.get_row_data())
                    
                    if data_list:
                        df = pd.DataFrame(data_list, columns=rs.fields)
                        spot_data = df.iloc[0].to_dict()
                        result[code] = spot_data
                        
                        # 保存到缓存
                        if self.enable_cache and self.cache:
                            self.cache.save_spot_data(code, spot_data)
            
            return result
            
        except Exception as e:
            print(f"批量获取实时行情失败: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_batch_index_data(self, codes: list) -> dict:
        """
        批量获取指数数据
        
        Args:
            codes: 指数代码列表 (如: ['000001', '000300'])
            
        Returns:
            字典，key为指数代码，value为行情数据
        """
        try:
            result = {}
            
            if not codes:
                return result
            
            # 从今天开始往前查找最近的交易日
            for i in range(30):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                
                for code in codes:
                    if code in result:
                        continue
                    
                    # 标准化代码格式
                    code_with_prefix = code
                    if '.' not in code:
                        if code.startswith('000') or code.startswith('399'):
                            code_with_prefix = f'sz.{code}'
                        elif code.startswith('sh.'):
                            code_with_prefix = code
                        else:
                            code_with_prefix = f'sh.{code}'
                    
                    # 尝试从缓存获取
                    if self.enable_cache and self.cache:
                        cached_data = self.cache.get_spot_data(f"index_{code}", max_age_hours=1)
                        if cached_data is not None:
                            result[code] = cached_data
                            continue
                    
                    rs = bs.query_history_k_data_plus(
                        code_with_prefix,
                        "date,code,open,high,low,close,volume,amount,pctChg",
                        start_date=date,
                        end_date=date,
                        frequency="d",
                        adjustflag="3"
                    )
                    
                    if rs.error_code != '0':
                        continue
                    
                    data_list = []
                    while (rs.error_code == '0') & rs.next():
                        data_list.append(rs.get_row_data())
                    
                    if data_list:
                        df = pd.DataFrame(data_list, columns=rs.fields)
                        index_data = df.iloc[0].to_dict()
                        result[code] = index_data
                        
                        # 保存到缓存
                        if self.enable_cache and self.cache:
                            self.cache.save_spot_data(f"index_{code}", index_data)
                
                # 如果所有指数都获取到了数据，提前退出
                if len(result) == len(codes):
                    break
            
            return result
            
        except Exception as e:
            print(f"批量获取指数数据失败: {e}")
            import traceback
            traceback.print_exc()
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
