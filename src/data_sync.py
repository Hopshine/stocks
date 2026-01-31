"""
股票行情数据同步服务
提供可靠的数据获取、错误处理和重试机制
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path
import traceback

from .config import API_CONFIG, LOG_CONFIG
from .baostock_fetcher import BaoStockDataFetcher
from .cache import StockDataCache

# 确保日志目录存在
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)


class SyncLogger:
    """同步日志管理器"""
    
    def __init__(self, name: str = 'stock_sync'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_CONFIG['level'])
        
        # 同步日志处理器
        sync_handler = logging.FileHandler(
            LOG_CONFIG.get('sync_log', log_dir / 'sync.log'),
            encoding='utf-8'
        )
        sync_handler.setLevel(logging.INFO)
        sync_handler.setFormatter(logging.Formatter(LOG_CONFIG['format']))
        
        # 错误日志处理器
        error_handler = logging.FileHandler(
            LOG_CONFIG.get('error_log', log_dir / 'error.log'),
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(LOG_CONFIG['format']))
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(LOG_CONFIG['format']))
        
        self.logger.addHandler(sync_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str, exc_info: bool = True):
        self.logger.error(message, exc_info=exc_info)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def success(self, message: str):
        self.logger.info(f"✓ {message}")
    
    def start_task(self, task_name: str):
        self.logger.info(f"🚀 开始执行任务: {task_name}")
    
    def end_task(self, task_name: str, status: str, details: str = ""):
        if status == 'success':
            self.logger.info(f"✅ 任务完成: {task_name} - {details}")
        else:
            self.logger.error(f"❌ 任务失败: {task_name} - {details}")


class DataSyncService:
    """股票数据同步服务"""
    
    def __init__(self, cache_path: str = "data/stock_cache.db", use_akshare: bool = False):
        """
        初始化数据同步服务
        
        Args:
            cache_path: 缓存数据库路径
            use_akshare: 是否使用akshare（更快），False则使用baostock
        """
        self.cache = StockDataCache(cache_path)
        self.fetcher = None
        self.use_akshare = use_akshare
        self.logger = SyncLogger()
        
        if use_akshare:
            self.config = API_CONFIG['akshare']
        else:
            self.config = API_CONFIG['baostock']
        
        self.retry_times = self.config['retry_times']
        self.retry_interval = self.config['retry_interval_seconds']
        
        # 同步状态
        self.sync_status = {
            'last_stock_list_sync': None,
            'last_market_data_sync': None,
            'last_index_data_sync': None,
            'sync_in_progress': False,
            'errors': []
        }
    
    def _get_fetcher(self):
        """获取数据获取器（懒加载）"""
        if self.fetcher is None:
            try:
                if self.use_akshare:
                    from src.data_fetcher import StockDataFetcher
                    self.fetcher = StockDataFetcher()
                    self.logger.info("使用akshare数据源（东方财富，速度更快）")
                else:
                    self.fetcher = BaoStockDataFetcher()
                    self.logger.info("使用baostock数据源")
            except Exception as e:
                self.logger.error(f"初始化数据获取器失败: {e}")
                return None
        return self.fetcher
    
    def _retry_sync(self, sync_func, *args, **kwargs) -> tuple:
        """
        带重试机制的同步（支持指数退避）
        
        Args:
            sync_func: 同步函数
            *args, **kwargs: 函数参数
            
        Returns:
            (success: bool, result: Any, error: str)
        """
        last_error = ""
        
        for attempt in range(1, self.retry_times + 1):
            try:
                result = sync_func(*args, **kwargs)
                return True, result, ""
            except Exception as e:
                last_error = str(e)
                if attempt < self.retry_times:
                    # 指数退避策略：每次重试等待时间加倍
                    wait_time = self.retry_interval * (2 ** (attempt - 1))
                    self.logger.warning(f"第 {attempt} 次尝试失败，{wait_time}秒后重试（指数退避）...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"尝试 {self.retry_times} 次后仍失败: {e}")
        
        return False, None, last_error
    
    def sync_stock_list(self) -> Dict[str, Any]:
        """
        同步股票列表
        
        Returns:
            同步结果信息
        """
        task_name = "同步股票列表"
        self.logger.start_task(task_name)
        
        start_time = datetime.now()
        result = {
            'task': task_name,
            'start_time': start_time.isoformat(),
            'success': False,
            'total_stocks': 0,
            'errors': [],
            'duration_seconds': 0
        }
        
        fetcher = self._get_fetcher()
        if fetcher is None:
            result['errors'].append("无法获取数据获取器")
            result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            self.logger.end_task(task_name, 'failed', str(result))
            return result
        
        success, data, error = self._retry_sync(fetcher.get_stock_list)
        
        if success and not data.empty:
            result['success'] = True
            result['total_stocks'] = len(data)
            result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            self.sync_status['last_stock_list_sync'] = datetime.now()
            self.logger.success(f"同步股票列表成功，共 {len(data)} 只股票")
        else:
            result['errors'].append(error)
            result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            self.logger.end_task(task_name, 'failed', str(result))
        
        return result
    
    def sync_market_data(self, codes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        同步实时行情数据（使用一次API调用获取所有股票）
        
        Args:
            codes: 股票代码列表，如果为None则同步所有股票
            
        Returns:
            同步结果信息
        """
        task_name = "同步实时行情"
        self.logger.start_task(task_name)
        
        start_time = datetime.now()
        result = {
            'task': task_name,
            'start_time': start_time.isoformat(),
            'success': False,
            'total_stocks': 0,
            'success_count': 0,
            'failed_count': 0,
            'errors': [],
            'duration_seconds': 0
        }
        
        fetcher = self._get_fetcher()
        if fetcher is None:
            result['errors'].append("无法获取数据获取器")
            result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            self.logger.end_task(task_name, 'failed', str(result))
            return result
        
        if self.use_akshare:
            # akshare: 使用一次API调用获取所有数据（1秒内完成）
            try:
                self.logger.info("使用 stock_zh_a_spot_em() 一次性获取全市场数据...")
                
                df = fetcher.get_daily_snapshot()
                
                if df.empty:
                    result['errors'].append("获取市场数据失败")
                    result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                    self.logger.end_task(task_name, 'failed', str(result))
                    return result
                
                # 逐条保存到缓存
                if self.cache:
                    saved_count = 0
                    for _, row in df.iterrows():
                        code = row.get('code')
                        if code:
                            spot_data = row.to_dict()
                            try:
                                self.cache.save_spot_data(code, spot_data)
                                saved_count += 1
                            except Exception as save_error:
                                self.logger.warning(f"保存 {code} 数据失败: {save_error}")
                    
                    self.logger.success(f"保存 {saved_count}/{len(df)} 只股票数据到缓存")
                
                result['success'] = True
                result['total_stocks'] = len(df)
                result['success_count'] = len(df)
                result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                self.sync_status['last_market_data_sync'] = datetime.now()
                self.logger.success(f"同步实时行情成功，共 {len(df)} 只股票，耗时 {result['duration_seconds']:.2f}秒")
                
            except Exception as e:
                result['errors'].append(str(e))
                result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                self.logger.end_task(task_name, 'failed', str(result))
        else:
            # baostock: 使用分批获取方法（原有逻辑）
            if codes is None:
                try:
                    stock_list = fetcher.get_stock_list()
                    codes = stock_list['code'].tolist()
                    self.logger.info(f"准备同步 {len(codes)} 只股票的实时行情")
                except Exception as e:
                    result['errors'].append(f"获取股票列表失败: {e}")
                    result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                    self.logger.end_task(task_name, 'failed', str(result))
                    return result
            
            result['total_stocks'] = len(codes)
            
            batch_size = 200  # 减少批次大小，避免触发服务器限制
            all_data = {}
            total_batches = (len(codes) + batch_size - 1) // batch_size
            
            for i in range(0, len(codes), batch_size):
                batch_codes = codes[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                self.logger.info(f"正在同步第 {batch_num}/{total_batches} 批次，共 {len(batch_codes)} 只股票")
                
                success, data, error = self._retry_sync(fetcher.get_batch_spot_data, batch_codes)
                
                if success:
                    all_data.update(data)
                    if self.cache:
                        for code, spot_data in data.items():
                            self.cache.save_spot_data(code, spot_data)
                    self.logger.success(f"第 {batch_num} 批次完成，成功 {len(data)}/{len(batch_codes)} 只")
                else:
                    result['errors'].append(f"批次 {batch_num}: {error}")
                
                # 增加批次之间的冷却时间，避免服务器限制
                if batch_num < total_batches:
                    cooling_time = 15  # 批次之间冷却15秒
                    self.logger.info(f"批次 {batch_num} 完成，冷却 {cooling_time} 秒后开始下一批次...")
                    time.sleep(cooling_time)
            
            result['success'] = True
            result['success_count'] = len(all_data)
            result['failed_count'] = len(codes) - len(all_data)
            result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            self.sync_status['last_market_data_sync'] = datetime.now()
            self.logger.success(f"同步实时行情完成，成功 {len(all_data)}/{len(codes)} 只，耗时 {result['duration_seconds']:.2f}秒")
        
        return result
    
    def sync_index_data(self) -> Dict[str, Any]:
        """
        同步指数数据
        
        Returns:
            同步结果信息
        """
        task_name = "同步指数数据"
        self.logger.start_task(task_name)
        
        start_time = datetime.now()
        result = {
            'task': task_name,
            'start_time': start_time.isoformat(),
            'success': False,
            'total_indices': 0,
            'errors': [],
            'duration_seconds': 0
        }
        
        fetcher = self._get_fetcher()
        if fetcher is None:
            result['errors'].append("无法获取数据获取器")
            result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            self.logger.end_task(task_name, 'failed', str(result))
            return result
        
        # 常用指数代码
        index_codes = [
            '000001',  # 上证指数
            '000300',  # 沪深300
            '000905',  # 中证500
            '399001',  # 深证成指
            '399006',  # 创业板指
            '399012',  # 创业板指
        ]
        
        success, data, error = self._retry_sync(fetcher.get_batch_index_data, index_codes)
        
        if success:
            result['success'] = True
            result['total_indices'] = len(data)
            result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            self.sync_status['last_index_data_sync'] = datetime.now()
            self.logger.success(f"同步指数数据成功，共 {len(data)} 个指数")
        else:
            result['errors'].append(error)
            result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            self.logger.end_task(task_name, 'failed', str(result))
        
        return result
    
    def sync_all(self) -> Dict[str, Any]:
        """
        执行完整的数据同步
        
        Returns:
            所有同步任务的综合结果
        """
        if self.sync_status['sync_in_progress']:
            self.logger.warning("同步任务已在进行中，跳过本次执行")
            return {'success': False, 'message': '同步任务已在进行中'}
        
        self.sync_status['sync_in_progress'] = True
        start_time = datetime.now()
        
        result = {
            'start_time': start_time.isoformat(),
            'success': True,
            'tasks': [],
            'total_duration_seconds': 0,
            'errors': []
        }
        
        try:
            # 同步股票列表
            list_result = self.sync_stock_list()
            result['tasks'].append(list_result)
            if not list_result['success']:
                result['success'] = False
                result['errors'].append(f"股票列表同步失败")
            
            # 同步实时行情
            market_result = self.sync_market_data()
            result['tasks'].append(market_result)
            if not market_result['success']:
                result['success'] = False
                result['errors'].append(f"实时行情同步失败")
            
            # 同步指数数据
            index_result = self.sync_index_data()
            result['tasks'].append(index_result)
            if not index_result['success']:
                result['success'] = False
                result['errors'].append(f"指数数据同步失败")
            
        except Exception as e:
            error_msg = f"同步过程发生异常: {e}"
            result['success'] = False
            result['errors'].append(error_msg)
            self.logger.error(error_msg, exc_info=True)
        
        finally:
            self.sync_status['sync_in_progress'] = False
            result['total_duration_seconds'] = (datetime.now() - start_time).total_seconds()
            
            if result['success']:
                self.logger.success(f"完整同步完成，耗时 {result['total_duration_seconds']:.2f}秒")
            else:
                self.logger.error(f"同步完成但存在错误: {result['errors']}")
        
        return result
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        return {
            'last_stock_list_sync': self.sync_status['last_stock_list_sync'].isoformat() if self.sync_status['last_stock_list_sync'] else None,
            'last_market_data_sync': self.sync_status['last_market_data_sync'].isoformat() if self.sync_status['last_market_data_sync'] else None,
            'last_index_data_sync': self.sync_status['last_index_data_sync'].isoformat() if self.sync_status['last_index_data_sync'] else None,
            'sync_in_progress': self.sync_status['sync_in_progress'],
            'cache_info': self.cache.get_cache_info()
        }
    
    def cleanup_old_data(self, days: int = 30):
        """
        清理旧数据
        
        Args:
            days: 保留天数
        """
        self.logger.info(f"开始清理 {days} 天前的旧数据...")
        
        try:
            # 这里可以添加清理逻辑
            # 例如：清理超过指定天数的历史数据
            self.logger.success(f"数据清理完成")
        except Exception as e:
            self.logger.error(f"数据清理失败: {e}")
    
    def shutdown(self):
        """关闭服务"""
        if self.fetcher:
            try:
                self.fetcher._logout()
                self.logger.info("数据获取器已关闭")
            except Exception as e:
                self.logger.error(f"关闭数据获取器时出错: {e}")


if __name__ == '__main__':
    # 测试同步服务
    print("=" * 60)
    print("股票数据同步服务 - 测试运行")
    print("=" * 60)
    
    service = DataSyncService()
    
    # 测试同步股票列表
    print("\n1. 测试同步股票列表...")
    result1 = service.sync_stock_list()
    print(f"   成功: {result1['success']}, 股票数: {result1.get('total_stocks', 0)}")
    
    # 测试同步实时行情
    print("\n2. 测试同步实时行情...")
    result2 = service.sync_market_data(['600000', '600036', '601398'])
    print(f"   成功: {result2['success']}, 成功数: {result2.get('success_count', 0)}")
    
    # 获取同步状态
    print("\n3. 同步状态:")
    status = service.get_sync_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    service.shutdown()
    print("\n测试完成！")
