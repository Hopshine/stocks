"""
baostock 全局登录管理器
确保在整个应用程序中共享同一个登录会话
"""
import baostock as bs
import threading

_lock = threading.Lock()
_login_count = 0
_lg = None


def global_login():
    """全局登录"""
    global _login_count, _lg
    
    with _lock:
        if _login_count == 0:
            _lg = bs.login()
            if _lg.error_code != '0':
                raise Exception(f"登录baostock失败: {_lg.error_msg}")
        _login_count += 1
        return _lg


def global_logout():
    """全局登出"""
    global _login_count, _lg
    
    with _lock:
        _login_count -= 1
        if _login_count <= 0:
            if _lg:
                try:
                    bs.logout()
                except Exception:
                    pass
                _lg = None
            _login_count = 0


def get_login():
    """获取当前登录状态"""
    global _login_count
    return _login_count > 0
