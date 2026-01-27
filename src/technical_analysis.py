"""
技术分析模块 - 计算各种技术指标
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict


class TechnicalAnalyzer:
    """技术分析器"""
    
    def __init__(self, df: pd.DataFrame):
        """
        初始化
        
        Args:
            df: 包含OHLCV数据的DataFrame
        """
        self.df = df.copy()
        self._validate_data()
    
    def _validate_data(self):
        """验证数据格式"""
        required_cols = ['open', 'close', 'high', 'low', 'volume']
        missing = [col for col in required_cols if col not in self.df.columns]
        if missing:
            raise ValueError(f"缺少必要的列: {missing}")
    
    # ==================== 移动平均线 ====================
    def ma(self, period: int = 20, column: str = 'close') -> pd.Series:
        """简单移动平均线"""
        return self.df[column].rolling(window=period).mean()
    
    def ema(self, period: int = 20, column: str = 'close') -> pd.Series:
        """指数移动平均线"""
        return self.df[column].ewm(span=period, adjust=False).mean()
    
    def sma(self, period: int = 20, column: str = 'close') -> pd.Series:
        """平滑移动平均线"""
        return self.df[column].ewm(span=period, adjust=True).mean()
    
    def wma(self, period: int = 20, column: str = 'close') -> pd.Series:
        """加权移动平均线"""
        weights = np.arange(1, period + 1)
        return self.df[column].rolling(window=period).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )
    
    # ==================== MACD ====================
    def macd(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """
        MACD指标
        
        Returns:
            dict包含: macd_line, signal_line, histogram
        """
        ema_fast = self.ema(fast)
        ema_slow = self.ema(slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    # ==================== RSI ====================
    def rsi(self, period: int = 14) -> pd.Series:
        """
        相对强弱指标RSI
        
        Args:
            period: 计算周期
            
        Returns:
            RSI值 (0-100)
        """
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def rsi_6_12_24(self) -> pd.DataFrame:
        """常用RSI组合 (6, 12, 24)"""
        return pd.DataFrame({
            'rsi_6': self.rsi(6),
            'rsi_12': self.rsi(12),
            'rsi_24': self.rsi(24)
        })
    
    # ==================== KDJ ====================
    def kdj(
        self,
        n: int = 9,
        m1: int = 3,
        m2: int = 3
    ) -> pd.DataFrame:
        """
        KDJ随机指标
        
        Args:
            n: RSV计算周期
            m1: K值平滑因子
            m2: D值平滑因子
            
        Returns:
            DataFrame包含 K, D, J值
        """
        low_list = self.df['low'].rolling(window=n, min_periods=n).min()
        high_list = self.df['high'].rolling(window=n, min_periods=n).max()
        
        rsv = (self.df['close'] - low_list) / (high_list - low_list) * 100
        
        k = pd.Series(np.zeros(len(self.df)), index=self.df.index)
        d = pd.Series(np.zeros(len(self.df)), index=self.df.index)
        
        k.iloc[n-1] = rsv.iloc[n-1]
        d.iloc[n-1] = rsv.iloc[n-1]
        
        for i in range(n, len(self.df)):
            k.iloc[i] = m1/(m1+1) * k.iloc[i-1] + 1/(m1+1) * rsv.iloc[i]
            d.iloc[i] = m2/(m2+1) * d.iloc[i-1] + 1/(m2+1) * k.iloc[i]
        
        j = 3 * k - 2 * d
        
        return pd.DataFrame({'K': k, 'D': d, 'J': j})
    
    # ==================== BOLL ====================
    def boll(self, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """
        布林带 (Bollinger Bands)
        
        Args:
            period: 计算周期
            std_dev: 标准差倍数
            
        Returns:
            DataFrame包含 upper, middle, lower
        """
        middle = self.ma(period)
        std = self.df['close'].rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return pd.DataFrame({
            'upper': upper,
            'middle': middle,
            'lower': lower
        })
    
    # ==================== 成交量指标 ====================
    def volume_ma(self, period: int = 20) -> pd.Series:
        """成交量移动平均线"""
        return self.df['volume'].rolling(window=period).mean()
    
    def obv(self) -> pd.Series:
        """
        能量潮指标 (On Balance Volume)
        """
        obv = pd.Series(index=self.df.index, dtype=float)
        obv.iloc[0] = 0
        
        for i in range(1, len(self.df)):
            if self.df['close'].iloc[i] > self.df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + self.df['volume'].iloc[i]
            elif self.df['close'].iloc[i] < self.df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - self.df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    def volume_ratio(self, short_period: int = 5, long_period: int = 60) -> pd.Series:
        """
        量比指标
        """
        short_ma = self.df['volume'].rolling(window=short_period).mean()
        long_ma = self.df['volume'].rolling(window=long_period).mean()
        return short_ma / long_ma
    
    # ==================== 趋势指标 ====================
    def atr(self, period: int = 14) -> pd.Series:
        """
        平均真实波幅 (Average True Range)
        """
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def adx(self, period: int = 14) -> pd.DataFrame:
        """
        平均趋向指数 (Average Directional Index)
        """
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        # +DM 和 -DM
        plus_dm = high.diff()
        minus_dm = low.diff().abs()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        plus_dm[plus_dm <= minus_dm] = 0
        minus_dm[minus_dm <= plus_dm] = 0
        
        # 真实波幅
        tr = pd.concat([
            high - low,
            abs(high - close.shift()),
            abs(low - close.shift())
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        
        # +DI 和 -DI
        plus_di = 100 * plus_dm.rolling(window=period).mean() / atr
        minus_di = 100 * minus_dm.rolling(window=period).mean() / atr
        
        # DX 和 ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return pd.DataFrame({
            'plus_di': plus_di,
            'minus_di': minus_di,
            'adx': adx
        })
    
    # ==================== 波动率指标 ====================
    def bollinger_pct(self, period: int = 20) -> pd.Series:
        """
        布林带百分比 (%B)
        """
        boll = self.boll(period)
        return (self.df['close'] - boll['lower']) / (boll['upper'] - boll['lower'])
    
    def volatility(self, period: int = 20) -> pd.Series:
        """
        波动率 (标准差)
        """
        return self.df['close'].rolling(window=period).std() / self.df['close'] * 100
    
    # ==================== 动量指标 ====================
    def roc(self, period: int = 12) -> pd.Series:
        """
        变动率 (Rate of Change)
        """
        return (self.df['close'] - self.df['close'].shift(period)) / self.df['close'].shift(period) * 100
    
    def momentum(self, period: int = 10) -> pd.Series:
        """
        动量指标
        """
        return self.df['close'] - self.df['close'].shift(period)
    
    # ==================== 综合信号 ====================
    def generate_signals(self) -> pd.DataFrame:
        """
        生成综合技术分析信号
        
        Returns:
            DataFrame包含各种指标和信号
        """
        signals = pd.DataFrame(index=self.df.index)
        
        # 移动平均线
        signals['ma5'] = self.ma(5)
        signals['ma10'] = self.ma(10)
        signals['ma20'] = self.ma(20)
        signals['ma60'] = self.ma(60)
        
        # MACD
        macd_data = self.macd()
        signals['macd'] = macd_data['macd']
        signals['macd_signal'] = macd_data['signal']
        signals['macd_histogram'] = macd_data['histogram']
        
        # RSI
        signals['rsi'] = self.rsi()
        
        # KDJ
        kdj_data = self.kdj()
        signals['k'] = kdj_data['K']
        signals['d'] = kdj_data['D']
        signals['j'] = kdj_data['J']
        
        # 布林带
        boll_data = self.boll()
        signals['boll_upper'] = boll_data['upper']
        signals['boll_middle'] = boll_data['middle']
        signals['boll_lower'] = boll_data['lower']
        
        # 成交量
        signals['volume_ma20'] = self.volume_ma(20)
        
        # 趋势信号
        signals['trend'] = np.where(
            signals['ma5'] > signals['ma10'], 'UP', 'DOWN'
        )
        
        # MACD信号
        signals['macd_signal_type'] = np.where(
            signals['macd'] > signals['macd_signal'], 'BUY', 'SELL'
        )
        
        # RSI信号
        signals['rsi_signal'] = np.where(
            signals['rsi'] > 70, 'OVERBOUGHT',
            np.where(signals['rsi'] < 30, 'OVERSOLD', 'NEUTRAL')
        )
        
        # KDJ信号
        signals['kdj_signal'] = np.where(
            (signals['k'] > signals['d']) & (signals['k'].shift(1) <= signals['d'].shift(1)),
            'GOLDEN_CROSS',
            np.where(
                (signals['k'] < signals['d']) & (signals['k'].shift(1) >= signals['d'].shift(1)),
                'DEAD_CROSS',
                'NEUTRAL'
            )
        )
        
        return signals
    
    def get_latest_signals(self) -> Dict:
        """获取最新信号"""
        signals = self.generate_signals()
        if len(signals) == 0:
            return {}
        
        latest = signals.iloc[-1]
        return {
            'ma5': latest['ma5'],
            'ma10': latest['ma10'],
            'ma20': latest['ma20'],
            'macd': latest['macd'],
            'macd_signal': latest['macd_signal_type'],
            'rsi': latest['rsi'],
            'rsi_signal': latest['rsi_signal'],
            'k': latest['k'],
            'd': latest['d'],
            'j': latest['j'],
            'kdj_signal': latest['kdj_signal'],
            'trend': latest['trend']
        }


# 便捷函数
def analyze_stock(df: pd.DataFrame) -> Dict:
    """
    快速分析股票的便捷函数
    
    Args:
        df: 股票数据DataFrame
        
    Returns:
        包含分析结果的字典
    """
    analyzer = TechnicalAnalyzer(df)
    return analyzer.get_latest_signals()


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算所有技术指标
    
    Args:
        df: 股票数据DataFrame
        
    Returns:
        包含所有指标的DataFrame
    """
    analyzer = TechnicalAnalyzer(df)
    return analyzer.generate_signals()