"""
股票行情后台调度器
提供定时任务管理和自动更新功能
"""
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable
from pathlib import Path

from .config import SCHEDULER_CONFIG, LOG_CONFIG
from .data_sync import DataSyncService

# 确保日志目录存在
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)


class StockScheduler:
    """
    股票数据后台调度器
    
    支持功能：
    - 定时执行数据同步任务
    - 可配置更新间隔
    - 后台运行，不阻塞主程序
    - 任务状态监控
    - 优雅关闭
    """
    
    def __init__(self, auto_start: bool = SCHEDULER_CONFIG['auto_start']):
        """
        初始化调度器
        
        Args:
            auto_start: 是否自动开始调度
        """
        self.logger = logging.getLogger('stock_scheduler')
        self.logger.setLevel(LOG_CONFIG['level'])
        
        # 添加文件处理器
        handler = logging.FileHandler(
            log_dir / 'scheduler.log',
            encoding='utf-8'
        )
        handler.setFormatter(logging.Formatter(LOG_CONFIG['format']))
        self.logger.addHandler(handler)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_CONFIG['format']))
        self.logger.addHandler(console_handler)
        
        self.sync_service = DataSyncService()
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        
        # 任务配置
        self.config = SCHEDULER_CONFIG
        
        # 任务状态
        self.task_status = {
            'stock_list': {
                'last_run': None,
                'next_run': None,
                'running': False,
                'success': None,
                'duration': 0
            },
            'market_data': {
                'last_run': None,
                'next_run': None,
                'running': False,
                'success': None,
                'duration': 0
            },
            'index_data': {
                'last_run': None,
                'next_run': None,
                'running': False,
                'success': None,
                'duration': 0
            }
        }
        
        # 调度器线程
        self._scheduler_thread: Optional[threading.Thread] = None
        
        if auto_start:
            self.start()
    
    def _log(self, level: str, message: str):
        """日志记录"""
        getattr(self.logger, level)(message)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{level.upper()}] {message}")
    
    def _calculate_next_run(self, interval_minutes: int) -> datetime:
        """计算下次运行时间"""
        return datetime.now() + timedelta(minutes=interval_minutes)
    
    def _run_sync_task(self, task_name: str, task_func: Callable, task_key: str):
        """
        执行同步任务
        
        Args:
            task_name: 任务名称
            task_func: 任务函数
            task_key: 任务状态key
        """
        if self.task_status[task_key]['running']:
            self._log('warning', f"任务 {task_name} 已在运行中，跳过本次执行")
            return
        
        self.task_status[task_key]['running'] = True
        self.task_status[task_key]['success'] = None
        
        start_time = datetime.now()
        self._log('info', f"🚀 开始执行任务: {task_name}")
        
        try:
            result = task_func()
            
            if result['success']:
                self.task_status[task_key]['success'] = True
                self._log('success', f"✅ 任务完成: {task_name} - 耗时 {result['duration_seconds']:.2f}秒")
                
                # 记录详细信息
                if task_key == 'stock_list':
                    self._log('info', f"   同步股票列表: {result.get('total_stocks', 0)} 只")
                elif task_key == 'market_data':
                    self._log('info', f"   同步实时行情: {result.get('success_count', 0)}/{result.get('total_stocks', 0)} 只")
                elif task_key == 'index_data':
                    self._log('info', f"   同步指数数据: {result.get('total_indices', 0)} 个")
            else:
                self.task_status[task_key]['success'] = False
                errors = result.get('errors', [])
                self._log('error', f"❌ 任务失败: {task_name} - {errors}")
        
        except Exception as e:
            self.task_status[task_key]['success'] = False
            self._log('error', f"❌ 任务异常: {task_name} - {str(e)}")
        
        finally:
            self.task_status[task_key]['last_run'] = datetime.now()
            self.task_status[task_key]['duration'] = (datetime.now() - start_time).total_seconds()
            self.task_status[task_key]['running'] = False
    
    def _scheduler_loop(self):
        """调度器主循环"""
        self._log('info', "📅 调度器已启动")
        
        # 初始化下次运行时间
        self.task_status['stock_list']['next_run'] = self._calculate_next_run(
            self.config['stock_list_interval_hours'] * 60
        )
        self.task_status['market_data']['next_run'] = self._calculate_next_run(
            self.config['market_data_interval_minutes']
        )
        self.task_status['index_data']['next_run'] = self._calculate_next_run(
            self.config['index_data_interval_minutes']
        )
        
        while self.running:
            try:
                now = datetime.now()
                
                # 检查股票列表同步任务
                if now >= self.task_status['stock_list']['next_run'] and \
                   not self.task_status['stock_list']['running']:
                    
                    # 在新线程中执行任务
                    thread = threading.Thread(
                        target=self._run_sync_task,
                        args=("同步股票列表", self.sync_service.sync_stock_list, 'stock_list'),
                        daemon=True
                    )
                    thread.start()
                    
                    # 更新下次运行时间
                    self.task_status['stock_list']['next_run'] = self._calculate_next_run(
                        self.config['stock_list_interval_hours'] * 60
                    )
                
                # 检查实时行情同步任务
                if now >= self.task_status['market_data']['next_run'] and \
                   not self.task_status['market_data']['running']:
                    
                    thread = threading.Thread(
                        target=self._run_sync_task,
                        args=("同步实时行情", self.sync_service.sync_market_data, 'market_data'),
                        daemon=True
                    )
                    thread.start()
                    
                    self.task_status['market_data']['next_run'] = self._calculate_next_run(
                        self.config['market_data_interval_minutes']
                    )
                
                # 检查指数数据同步任务
                if now >= self.task_status['index_data']['next_run'] and \
                   not self.task_status['index_data']['running']:
                    
                    thread = threading.Thread(
                        target=self._run_sync_task,
                        args=("同步指数数据", self.sync_service.sync_index_data, 'index_data'),
                        daemon=True
                    )
                    thread.start()
                    
                    self.task_status['index_data']['next_run'] = self._calculate_next_run(
                        self.config['index_data_interval_minutes']
                    )
                
                # 休眠1分钟
                time.sleep(60)
                
            except Exception as e:
                self._log('error', f"调度器循环异常: {str(e)}")
                time.sleep(10)  # 发生异常时短暂休眠
        
        self._log('info', "📅 调度器已停止")
    
    def start(self):
        """启动调度器"""
        if self.running:
            self._log('warning', "调度器已在运行中")
            return
        
        self.running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        self._log('info', "🚀 调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if not self.running:
            return
        
        self.running = False
        
        # 等待当前任务完成
        max_wait = 30  # 最多等待30秒
        start_time = time.time()
        
        while any(task['running'] for task in self.task_status.values()):
            if time.time() - start_time > max_wait:
                self._log('warning', "等待任务完成超时，强制停止")
                break
            time.sleep(1)
        
        # 关闭同步服务
        self.sync_service.shutdown()
        
        self._log('info', "🛑 调度器已停止")
    
    def trigger_sync(self, task_type: str = 'all') -> dict:
        """
        手动触发同步任务
        
        Args:
            task_type: 任务类型 (all/stock_list/market_data/index_data)
            
        Returns:
            同步结果
        """
        if task_type == 'all':
            return self.sync_service.sync_all()
        elif task_type == 'stock_list':
            return self.sync_service.sync_stock_list()
        elif task_type == 'market_data':
            return self.sync_service.sync_market_data()
        elif task_type == 'index_data':
            return self.sync_service.sync_index_data()
        else:
            return {'success': False, 'error': f'未知任务类型: {task_type}'}
    
    def get_status(self) -> dict:
        """获取调度器状态"""
        status = {
            'running': self.running,
            'config': self.config,
            'tasks': {}
        }
        
        for task_key, task_info in self.task_status.items():
            status['tasks'][task_key] = {
                'last_run': task_info['last_run'].isoformat() if task_info['last_run'] else None,
                'next_run': task_info['next_run'].isoformat() if task_info['next_run'] else None,
                'running': task_info['running'],
                'success': task_info['success'],
                'duration': task_info['duration']
            }
        
        # 添加缓存信息
        try:
            status['cache'] = self.sync_service.cache.get_cache_info()
        except Exception:
            status['cache'] = {'error': '无法获取缓存信息'}
        
        return status
    
    def update_config(self, **kwargs):
        """
        更新调度配置
        
        Args:
            **kwargs: 配置参数
        """
        valid_keys = [
            'stock_list_interval_hours',
            'market_data_interval_minutes',
            'index_data_interval_minutes',
            'auto_start'
        ]
        
        for key, value in kwargs.items():
            if key in valid_keys:
                self.config[key] = value
                self._log('info', f"配置已更新: {key} = {value}")
            else:
                self._log('warning', f"未知配置项: {key}")


# 全局调度器实例
_scheduler: Optional[StockScheduler] = None


def get_scheduler(auto_start: bool = False) -> StockScheduler:
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = StockScheduler(auto_start=auto_start)
    return _scheduler


def start_scheduler():
    """启动全局调度器"""
    global _scheduler
    if _scheduler is None:
        _scheduler = StockScheduler(auto_start=True)
    else:
        _scheduler.start()


def stop_scheduler():
    """停止全局调度器"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.stop()


if __name__ == '__main__':
    print("=" * 60)
    print("股票数据调度器 - 测试运行")
    print("=" * 60)
    
    scheduler = StockScheduler(auto_start=False)
    
    # 手动触发一次同步
    print("\n1. 手动触发股票列表同步...")
    result1 = scheduler.trigger_sync('stock_list')
    print(f"   成功: {result1['success']}")
    
    print("\n2. 手动触发实时行情同步...")
    result2 = scheduler.trigger_sync('market_data')
    print(f"   成功: {result2['success']}")
    
    print("\n3. 手动触发指数数据同步...")
    result3 = scheduler.trigger_sync('index_data')
    print(f"   成功: {result3['success']}")
    
    print("\n4. 获取调度器状态...")
    status = scheduler.get_status()
    print(f"   运行状态: {'运行中' if status['running'] else '已停止'}")
    
    for task_name, task_status in status['tasks'].items():
        print(f"\n   {task_name}:")
        print(f"      最后运行: {task_status['last_run']}")
        print(f"      下次运行: {task_status['next_run']}")
        print(f"      运行状态: {'运行中' if task_status['running'] else '空闲'}")
        print(f"      上次结果: {'成功' if task_status['success'] else ('失败' if task_status['success'] is False else '未运行')}")
        print(f"      耗时: {task_status['duration']:.2f}秒")
    
    scheduler.stop()
    print("\n测试完成！")
