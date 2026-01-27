"""
选股策略模块 - 实现多种选股策略
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from .data_fetcher import StockDataFetcher
from .baostock_fetcher import BaoStockDataFetcher
from .technical_analysis import TechnicalAnalyzer


class StockStrategy:
    """选股策略基类"""
    
    def __init__(self, fetcher=None):
        if fetcher is None:
            self.fetcher = BaoStockDataFetcher()
        else:
            self.fetcher = fetcher
    
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """
        筛选股票
        
        Args:
            stocks_df: 股票列表DataFrame
            
        Returns:
            筛选后的DataFrame
        """
        raise NotImplementedError("子类必须实现此方法")


class MACDStrategy(StockStrategy):
    """MACD金叉策略"""
    
    def filter(self, stocks_df: pd.DataFrame, days: int = 5) -> pd.DataFrame:
        """
        筛选MACD金叉的股票
        
        Args:
            stocks_df: 股票列表
            days: 获取历史数据的天数
            
        Returns:
            符合条件的股票
        """
        results = []
        
        for _, row in stocks_df.iterrows():
            try:
                code = row['code']
                # 获取历史数据
                df = self.fetcher.get_historical_data(code, days=days)
                
                if len(df) < 26:  # MACD需要至少26天数据
                    continue
                
                # 计算MACD
                analyzer = TechnicalAnalyzer(df)
                macd_data = analyzer.macd()
                
                # 检查金叉
                macd = macd_data['macd']
                signal = macd_data['signal']
                
                # 当前MACD > Signal, 且前一天 MACD <= Signal
                if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
                    results.append({
                        'code': code,
                        'name': row['name'],
                        'macd': macd.iloc[-1],
                        'signal': signal.iloc[-1],
                        'price': df['close'].iloc[-1]
                    })
            except Exception as e:
                continue
        
        return pd.DataFrame(results)


class RSIStrategy(StockStrategy):
    """RSI超卖策略"""
    
    def __init__(self, oversold_threshold: float = 30):
        super().__init__()
        self.oversold_threshold = oversold_threshold
    
    def filter(self, stocks_df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
        """
        筛选RSI超卖的股票
        
        Returns:
            RSI < 阈值的股票
        """
        results = []
        
        for _, row in stocks_df.iterrows():
            try:
                code = row['code']
                df = self.fetcher.get_historical_data(code, days=days)
                
                if len(df) < 14:
                    continue
                
                analyzer = TechnicalAnalyzer(df)
                rsi = analyzer.rsi()
                
                latest_rsi = rsi.iloc[-1]
                
                if latest_rsi < self.oversold_threshold:
                    results.append({
                        'code': code,
                        'name': row['name'],
                        'rsi': latest_rsi,
                        'price': df['close'].iloc[-1]
                    })
            except Exception:
                continue
        
        return pd.DataFrame(results)


class BollingerStrategy(StockStrategy):
    """布林带策略 - 触及下轨买入"""
    
    def filter(self, stocks_df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
        """
        筛选触及布林带下轨的股票
        
        Returns:
            触及下轨的股票
        """
        results = []
        
        for _, row in stocks_df.iterrows():
            try:
                code = row['code']
                df = self.fetcher.get_historical_data(code, days=days)
                
                if len(df) < 20:
                    continue
                
                analyzer = TechnicalAnalyzer(df)
                boll = analyzer.boll()
                
                close = df['close'].iloc[-1]
                lower = boll['lower'].iloc[-1]
                upper = boll['upper'].iloc[-1]
                
                # 价格接近或低于下轨
                if close <= lower * 1.02:  # 允许2%的误差
                    results.append({
                        'code': code,
                        'name': row['name'],
                        'close': close,
                        'lower': lower,
                        'upper': upper,
                        'boll_pct': (close - lower) / (upper - lower) * 100
                    })
            except Exception:
                continue
        
        return pd.DataFrame(results)


class GoldenCrossStrategy(StockStrategy):
    """均线金叉策略"""
    
    def __init__(self, short_ma: int = 5, long_ma: int = 20):
        super().__init__()
        self.short_ma = short_ma
        self.long_ma = long_ma
    
    def filter(self, stocks_df: pd.DataFrame, days: int = 60) -> pd.DataFrame:
        """
        筛选均线金叉的股票
        
        Returns:
            金叉股票
        """
        results = []
        
        for _, row in stocks_df.iterrows():
            try:
                code = row['code']
                df = self.fetcher.get_historical_data(code, days=days)
                
                if len(df) < self.long_ma + 5:
                    continue
                
                analyzer = TechnicalAnalyzer(df)
                
                short = analyzer.ma(self.short_ma)
                long = analyzer.ma(self.long_ma)
                
                # 金叉判断
                if (short.iloc[-1] > long.iloc[-1] and 
                    short.iloc[-2] <= long.iloc[-2]):
                    results.append({
                        'code': code,
                        'name': row['name'],
                        f'ma{self.short_ma}': short.iloc[-1],
                        f'ma{self.long_ma}': long.iloc[-1],
                        'price': df['close'].iloc[-1]
                    })
            except Exception:
                continue
        
        return pd.DataFrame(results)


class VolumeBreakoutStrategy(StockStrategy):
    """放量突破策略"""
    
    def __init__(self, volume_ratio: float = 2.0):
        super().__init__()
        self.volume_ratio = volume_ratio
    
    def filter(self, stocks_df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
        """
        筛选放量上涨的股票
        
        Returns:
            放量股票
        """
        results = []
        
        for _, row in stocks_df.iterrows():
            try:
                code = row['code']
                df = self.fetcher.get_historical_data(code, days=days)
                
                if len(df) < 20:
                    continue
                
                # 今日成交量 vs 20日平均成交量
                today_volume = df['volume'].iloc[-1]
                avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
                
                # 今日涨幅
                today_change = df['pct_change'].iloc[-1]
                
                # 放量且上涨
                if (today_volume / avg_volume > self.volume_ratio and 
                    today_change > 3):
                    results.append({
                        'code': code,
                        'name': row['name'],
                        'volume_ratio': today_volume / avg_volume,
                        'change': today_change,
                        'price': df['close'].iloc[-1]
                    })
            except Exception:
                continue
        
        return pd.DataFrame(results)


class MultiIndicatorStrategy(StockStrategy):
    """多指标综合策略"""
    
    def filter(self, stocks_df: pd.DataFrame, days: int = 60) -> pd.DataFrame:
        """
        多指标综合筛选
        
        条件:
        1. MACD金叉或多头排列
        2. RSI不在超买区 (<70)
        3. 价格在布林带上轨附近
        4. 成交量放大
        
        Returns:
            综合评分高的股票
        """
        results = []
        
        for _, row in stocks_df.iterrows():
            try:
                code = row['code']
                df = self.fetcher.get_historical_data(code, days=days)
                
                if len(df) < 60:
                    continue
                
                analyzer = TechnicalAnalyzer(df)
                score = 0
                signals = {}
                
                # 1. MACD判断
                macd_data = analyzer.macd()
                macd = macd_data['macd']
                signal = macd_data['signal']
                
                if macd.iloc[-1] > signal.iloc[-1]:
                    score += 25
                    signals['macd'] = 'BULL'
                    if macd.iloc[-2] <= signal.iloc[-2]:
                        score += 10
                        signals['macd'] = 'GOLDEN_CROSS'
                else:
                    signals['macd'] = 'BEAR'
                
                # 2. RSI判断
                rsi = analyzer.rsi()
                latest_rsi = rsi.iloc[-1]
                
                if 30 <= latest_rsi <= 70:
                    score += 25
                    signals['rsi'] = 'NORMAL'
                elif latest_rsi < 30:
                    score += 15
                    signals['rsi'] = 'OVERSOLD'
                else:
                    signals['rsi'] = 'OVERBOUGHT'
                
                # 3. 布林带判断
                boll = analyzer.boll()
                close = df['close'].iloc[-1]
                upper = boll['upper'].iloc[-1]
                middle = boll['middle'].iloc[-1]
                lower = boll['lower'].iloc[-1]
                
                boll_pct = (close - lower) / (upper - lower)
                
                if 0.4 <= boll_pct <= 0.8:
                    score += 25
                    signals['boll'] = 'MIDDLE_UPPER'
                elif boll_pct > 0.8:
                    score += 15
                    signals['boll'] = 'NEAR_UPPER'
                elif boll_pct < 0.4:
                    signals['boll'] = 'LOWER_HALF'
                
                # 4. 成交量判断
                vol_ratio = df['volume'].iloc[-1] / df['volume'].rolling(20).mean().iloc[-1]
                
                if vol_ratio > 1.5:
                    score += 25
                    signals['volume'] = 'HIGH'
                elif vol_ratio > 1.0:
                    score += 15
                    signals['volume'] = 'NORMAL'
                else:
                    signals['volume'] = 'LOW'
                
                signals['volume_ratio'] = vol_ratio
                
                # 5. 均线排列
                ma5 = analyzer.ma(5).iloc[-1]
                ma10 = analyzer.ma(10).iloc[-1]
                ma20 = analyzer.ma(20).iloc[-1]
                
                if ma5 > ma10 > ma20:
                    score += 15
                    signals['ma_trend'] = 'STRONG_BULL'
                elif ma5 > ma10:
                    score += 5
                    signals['ma_trend'] = 'WEAK_BULL'
                else:
                    signals['ma_trend'] = 'BEAR'
                
                # 总分高于60分入选
                if score >= 60:
                    results.append({
                        'code': code,
                        'name': row['name'],
                        'score': score,
                        'price': close,
                        **signals
                    })
            except Exception:
                continue
        
        df_result = pd.DataFrame(results)
        if not df_result.empty:
            df_result = df_result.sort_values('score', ascending=False)
        
        return df_result


class FundamentalStrategy(StockStrategy):
    """基本面选股策略"""
    
    def filter(
        self,
        stocks_df: pd.DataFrame,
        min_pe: Optional[float] = None,
        max_pe: Optional[float] = 30,
        min_pb: Optional[float] = None,
        max_pb: Optional[float] = 3,
        min_market_cap: Optional[float] = None,  # 亿元
        max_market_cap: Optional[float] = None
    ) -> pd.DataFrame:
        """
        基于基本面指标筛选
        
        Args:
            stocks_df: 股票列表
            min_pe: 最小市盈率
            max_pe: 最大市盈率
            min_pb: 最小市净率
            max_pb: 最大市净率
            min_market_cap: 最小市值(亿元)
            max_market_cap: 最大市值(亿元)
            
        Returns:
            符合条件的股票
        """
        df = stocks_df.copy()
        
        # 转换数据类型
        df['pe'] = pd.to_numeric(df['pe'], errors='coerce')
        df['pb'] = pd.to_numeric(df['pb'], errors='coerce')
        df['market_cap'] = pd.to_numeric(df['market_cap'], errors='coerce')
        
        # 应用筛选条件
        if min_pe is not None:
            df = df[df['pe'] >= min_pe]
        if max_pe is not None:
            df = df[df['pe'] <= max_pe]
        if min_pb is not None:
            df = df[df['pb'] >= min_pb]
        if max_pb is not None:
            df = df[df['pb'] <= max_pb]
        if min_market_cap is not None:
            df = df[df['market_cap'] >= min_market_cap * 1e8]
        if max_market_cap is not None:
            df = df[df['market_cap'] <= max_market_cap * 1e8]
        
        return df


class CompositeStrategy:
    """复合策略 - 组合多个策略"""
    
    def __init__(self):
        self.strategies = []
    
    def add_strategy(self, strategy: StockStrategy, weight: float = 1.0):
        """
        添加策略
        
        Args:
            strategy: 策略对象
            weight: 权重
        """
        self.strategies.append((strategy, weight))
    
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """
        执行所有策略并综合评分
        """
        all_results = []
        
        for strategy, weight in self.strategies:
            try:
                result = strategy.filter(stocks_df)
                if not result.empty:
                    result['strategy_weight'] = weight
                    all_results.append(result)
            except Exception:
                continue
        
        if not all_results:
            return pd.DataFrame()
        
        # 合并结果
        combined = pd.concat(all_results, ignore_index=True)
        
        # 按股票代码分组统计
        grouped = combined.groupby(['code', 'name']).agg({
            'strategy_weight': 'sum',
            'score': 'mean' if 'score' in combined.columns else 'count'
        }).reset_index()
        
        grouped = grouped.sort_values('strategy_weight', ascending=False)
        
        return grouped


# 便捷函数
def find_macd_golden_cross(stocks_df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
    """查找MACD金叉股票"""
    strategy = MACDStrategy()
    return strategy.filter(stocks_df, days)


def find_rsi_oversold(stocks_df: pd.DataFrame, threshold: float = 30) -> pd.DataFrame:
    """查找RSI超卖股票"""
    strategy = RSIStrategy(threshold)
    return strategy.filter(stocks_df)


def find_golden_cross(stocks_df: pd.DataFrame, short: int = 5, long: int = 20) -> pd.DataFrame:
    """查找均线金叉股票"""
    strategy = GoldenCrossStrategy(short, long)
    return strategy.filter(stocks_df)


def find_volume_breakout(stocks_df: pd.DataFrame, ratio: float = 2.0) -> pd.DataFrame:
    """查找放量突破股票"""
    strategy = VolumeBreakoutStrategy(ratio)
    return strategy.filter(stocks_df)


def multi_screening(stocks_df: pd.DataFrame) -> pd.DataFrame:
    """多指标综合选股"""
    strategy = MultiIndicatorStrategy()
    return strategy.filter(stocks_df)