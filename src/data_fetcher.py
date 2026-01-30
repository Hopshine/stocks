"""
股票数据获取模块 - 使用akshare获取A股数据
"""
import os
import sys

# 在导入任何其他模块之前清除代理环境变量
_proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
               'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
for _var in _proxy_vars:
    if _var in os.environ:
        print(f"[data_fetcher] 清除代理环境变量: {_var}")
        del os.environ[_var]

# 现在导入其他模块
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import time
import requests
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 定义通用的请求头
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# 创建一个全局会话对象，不使用代理
session = requests.Session()
session.trust_env = False
session.proxies = {'http': None, 'https': None}
session.headers.update(DEFAULT_HEADERS)
session.verify = False  # 禁用SSL验证

# Monkey-patch requests.Session 来禁用代理和添加默认配置
_original_session_init = requests.Session.__init__
def _patched_session_init(self, *args, **kwargs):
    _original_session_init(self, *args, **kwargs)
    # 禁用代理
    self.trust_env = False
    # 清除代理配置
    self.proxies = {'http': None, 'https': None}
    # 设置超时
    self.timeout = (10, 30)  # (连接超时, 读取超时)
    # 添加默认请求头
    self.headers.update(DEFAULT_HEADERS)
    # 禁用SSL验证
    self.verify = False

requests.Session.__init__ = _patched_session_init

# Monkey-patch requests.request 来确保所有请求都不使用代理
_original_request = requests.request
def _patched_request(method, url, **kwargs):
    # 强制禁用代理
    kwargs['proxies'] = {'http': None, 'https': None}
    kwargs['trust_env'] = False
    kwargs['verify'] = False
    return _original_request(method, url, **kwargs)

requests.request = _patched_request

# 最后导入akshare（这样它会使用我们 patched 的 requests）
import akshare as ak


class StockDataFetcher:
    """A股数据获取器"""
    
    def __init__(self):
        self.retry_times = 5
        self.retry_delay = 2
        self.session = session
    
    def _clear_proxy_settings(self):
        """清除代理设置，避免代理连接问题"""
        # 清除环境变量中的代理设置
        for var in _proxy_vars:
            if var in os.environ:
                del os.environ[var]
    
    def _retry_fetch(self, func, *args, **kwargs):
        """带重试机制和指数退避的数据获取"""
        last_error = None
        for i in range(self.retry_times):
            try:
                # 每次重试前清除代理设置
                self._clear_proxy_settings()
                result = func(*args, **kwargs)
                
                # 检查返回结果是否为空DataFrame
                if isinstance(result, pd.DataFrame) and result.empty:
                    print(f"警告: {func.__name__} 返回空DataFrame")
                
                return result
                
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # 检查是否是连接相关错误
                is_connection_error = (
                    'proxy' in error_msg or 
                    'connection' in error_msg or
                    'timeout' in error_msg or
                    'remote' in error_msg or
                    'aborted' in error_msg or
                    'closed' in error_msg
                )
                
                if is_connection_error:
                    print(f"连接错误 (尝试 {i+1}/{self.retry_times}): {e}")
                    # 指数退避策略
                    wait_time = self.retry_delay * (2 ** i)
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    
                    if i == self.retry_times - 1:
                        print(f"达到最大重试次数 {self.retry_times}，返回空数据")
                        return None
                else:
                    # 非连接错误，直接抛出或返回
                    if i == self.retry_times - 1:
                        print(f"非连接错误，达到最大重试次数: {e}")
                        raise e
                    time.sleep(self.retry_delay)
        
        # 如果所有重试都失败
        return None
    
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取A股所有股票列表
        
        Returns:
            DataFrame包含: 代码, 名称, 所属行业等信息
        """
        try:
            # 获取上海和深圳股票列表，使用重试机制
            sh_stocks = self._retry_fetch(ak.stock_sh_a_spot_em)
            if sh_stocks is None or sh_stocks.empty:
                print("获取上海A股列表失败或返回空数据")
                sh_stocks = pd.DataFrame()
                
            sz_stocks = self._retry_fetch(ak.stock_sz_a_spot_em)
            if sz_stocks is None or sz_stocks.empty:
                print("获取深圳A股列表失败或返回空数据")
                sz_stocks = pd.DataFrame()
            
            # 如果两个都为空，直接返回空DataFrame
            if sh_stocks.empty and sz_stocks.empty:
                print("无法获取任何股票数据")
                return pd.DataFrame()
            
            # 合并并去重
            all_stocks = pd.concat([sh_stocks, sz_stocks], ignore_index=True)
            
            # 检查是否有'代码'列
            if '代码' not in all_stocks.columns:
                print(f"返回的数据列名不匹配，实际列名: {list(all_stocks.columns)}")
                return pd.DataFrame()
            
            all_stocks = all_stocks.drop_duplicates(subset=['代码'])
            
            # 定义列名映射
            columns_map = {
                '代码': 'code',
                '名称': 'name',
                '最新价': 'price',
                '涨跌幅': 'change_pct',
                '成交量': 'volume',
                '成交额': 'amount',
                '市盈率-动态': 'pe',
                '市净率': 'pb',
                '所属行业': 'industry',
                '总市值': 'market_cap',
                '流通市值': 'float_cap'
            }
            
            # 只重命名实际存在的列
            existing_columns = {k: v for k, v in columns_map.items() if k in all_stocks.columns}
            df = all_stocks.rename(columns=existing_columns)
            
            # 返回所有实际存在的列（使用新的列名）
            result_columns = list(existing_columns.values())
            return df[result_columns]
            
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_stock_spot(self, code: str) -> Dict:
        """
        获取单只股票的实时行情
        
        Args:
            code: 股票代码 (如: 000001, 600000)
            
        Returns:
            包含实时行情数据的字典
        """
        try:
            df = ak.stock_individual_spot_xq(symbol=code)
            return dict(zip(df['item'], df['value']))
        except Exception as e:
            print(f"获取股票 {code} 实时行情失败: {e}")
            return {}
    
    def get_all_spot_data(self) -> pd.DataFrame:
        """
        获取全市场实时行情（一次API调用获取所有股票）
        使用 stock_zh_a_spot_em() 替代分批获取，大幅提升速度
        
        Returns:
            DataFrame包含所有股票的实时数据
        """
        try:
            print("使用 stock_zh_a_spot_em() 获取全市场数据...")
            df = self._retry_fetch(ak.stock_zh_a_spot_em)
            
            if df is None or df.empty:
                print("获取全市场数据失败或返回空")
                return pd.DataFrame()
            
            print(f"成功获取 {len(df)} 只股票数据")
            return df
            
        except Exception as e:
            print(f"获取全市场实时行情失败: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_daily_snapshot(self) -> pd.DataFrame:
        """
        获取每日行情快照（结构化数据，用于缓存）
        整合实时数据，生成标准格式的每日数据
        
        Returns:
            DataFrame包含: code, name, price, change_pct, volume, amount, pe, pb等
        """
        df = self.get_all_spot_data()
        
        if df.empty:
            return pd.DataFrame()
        
        # 列名映射（东方财富原始列名 -> 标准列名）
        columns_map = {
            '代码': 'code',
            '名称': 'name',
            '最新价': 'price',
            '涨跌幅': 'change_pct',
            '涨跌额': 'change',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '最高': 'high',
            '最低': 'low',
            '今开': 'open',
            '昨收': 'pre_close',
            '市盈率-动态': 'pe',
            '市净率': 'pb',
            '总市值': 'market_cap',
            '流通市值': 'float_cap',
            '换手率': 'turnover'
        }
        
        # 只重命名存在的列
        existing_map = {k: v for k, v in columns_map.items() if k in df.columns}
        result = df.rename(columns=existing_map)
        
        # 提取存在的列
        wanted_cols = list(existing_map.values())
        available_cols = [c for c in wanted_cols if c in result.columns]
        
        return result[available_cols].copy()
    
    def get_historical_data(
        self,
        code: str,
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"  # qfq-前复权, hfq-后复权, 不复权
    ) -> pd.DataFrame:
        """
        获取股票历史K线数据
        
        Args:
            code: 股票代码
            period: 周期 (daily/weekly/monthly)
            start_date: 开始日期 (YYYYMMDD格式), 默认为一年前
            end_date: 结束日期 (YYYYMMDD格式), 默认为今天
            adjust: 复权类型
            
        Returns:
            DataFrame包含OHLCV数据
        """
        # 设置默认日期
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            # 标准化列名
            df.columns = [
                'date', 'open', 'close', 'high', 'low', 'volume',
                'amount', 'amplitude', 'pct_change', 'price_change',
                'turnover'
            ]
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"获取股票 {code} 历史数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_news(self, code: str, num: int = 20) -> pd.DataFrame:
        """
        获取股票相关新闻
        
        Args:
            code: 股票代码
            num: 获取条数
            
        Returns:
            DataFrame包含新闻标题、时间、内容摘要
        """
        try:
            df = ak.stock_news_em(symbol=code)
            return df.head(num)
        except Exception as e:
            print(f"获取股票 {code} 新闻失败: {e}")
            return pd.DataFrame()
    
    def get_financial_report(
        self,
        code: str,
        report_type: str = "profit"  # profit/revenue/cashflow/balance
    ) -> pd.DataFrame:
        """
        获取财务报表数据
        
        Args:
            code: 股票代码
            report_type: 报表类型 (profit-利润表, revenue-营收, cashflow-现金流, balance-资产负债表)
            
        Returns:
            DataFrame包含财务数据
        """
        try:
            if report_type == "profit":
                df = ak.stock_profit_sheet_by_report_em(symbol=code)
            elif report_type == "revenue":
                df = ak.stock_profit_sheet_by_report_em(symbol=code)
            else:
                df = ak.stock_financial_report_sina(stock=code)
            
            return df
            
        except Exception as e:
            print(f"获取股票 {code} 财务报表失败: {e}")
            return pd.DataFrame()
    
    def get_sector_stocks(self, sector: str) -> pd.DataFrame:
        """
        获取某个板块的所有股票
        
        Args:
            sector: 板块名称 (如: 银行, 医药制造, 房地产等)
            
        Returns:
            DataFrame包含该板块股票列表
        """
        try:
            all_stocks = self.get_stock_list()
            return all_stocks[all_stocks['industry'] == sector]
        except Exception as e:
            print(f"获取板块 {sector} 股票失败: {e}")
            return pd.DataFrame()
    
    def get_index_data(self, index_code: str = "000001") -> pd.DataFrame:
        """
        获取指数数据
        
        Args:
            index_code: 指数代码 (000001-上证指数, 399001-深证成指, 399006-创业板指)
            
        Returns:
            DataFrame包含指数历史数据
        """
        try:
            df = ak.index_zh_a_hist(symbol=index_code, period="daily")
            df.columns = [
                'date', 'open', 'close', 'high', 'low', 'volume',
                'amount', 'amplitude', 'pct_change', 'price_change',
                'turnover'
            ]
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df
        except Exception as e:
            print(f"获取指数 {index_code} 数据失败: {e}")
            return pd.DataFrame()
    
    def get_concept_stocks(self, concept: str) -> pd.DataFrame:
        """
        获取概念板块成分股
        
        Args:
            concept: 概念名称 (如: 人工智能, 新能源车, 芯片等)
            
        Returns:
            DataFrame包含该概念板块股票
        """
        try:
            # 先获取概念板块列表
            concept_list = ak.stock_board_concept_name_ths()
            
            if concept in concept_list['概念名称'].values:
                df = ak.stock_board_concept_cons_ths(symbol=concept)
                return df
            else:
                print(f"概念板块 {concept} 不存在")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"获取概念板块 {concept} 股票失败: {e}")
            return pd.DataFrame()
    
    def get_industry_ranking(self, sort_by: str = "change_pct") -> pd.DataFrame:
        """
        获取行业板块涨跌幅排行
        
        Args:
            sort_by: 排序字段
            
        Returns:
            DataFrame包含各行业板块数据
        """
        try:
            df = ak.stock_sector_spot(symbol="industry")
            return df
        except Exception as e:
            print(f"获取行业排行失败: {e}")
            return pd.DataFrame()


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
    fetcher = StockDataFetcher()
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    return fetcher.get_historical_data(code, start_date=start_date)


def fetch_market_data() -> pd.DataFrame:
    """
    获取全市场股票数据
    
    Returns:
        DataFrame包含所有A股数据
    """
    fetcher = StockDataFetcher()
    return fetcher.get_stock_list()