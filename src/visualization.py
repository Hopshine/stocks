"""
数据可视化模块 - 提供多种图表展示
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Tuple
from .technical_analysis import TechnicalAnalyzer
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class StockVisualizer:
    """股票数据可视化器"""
    
    def __init__(self, style: str = 'default'):
        self.style = style
        plt.style.use(style)
    
    def plot_kline(
        self,
        df: pd.DataFrame,
        title: str = "K线图",
        volume: bool = True,
        save_path: Optional[str] = None,
        figsize: Tuple[int, int] = (16, 10)
    ) -> None:
        """
        绘制K线图
        
        Args:
            df: 包含OHLCV数据的DataFrame
            title: 图表标题
            volume: 是否显示成交量
            save_path: 保存路径
            figsize: 图像尺寸
        """
        if volume:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, 
                                           gridspec_kw={'height_ratios': [3, 1]})
        else:
            fig, ax1 = plt.subplots(figsize=figsize)
            ax2 = None
        
        # 绘制K线
        self._draw_candles(ax1, df)
        
        # 绘制移动平均线
        if len(df) >= 60:
            ax1.plot(df.index, df['close'].rolling(5).mean(), 
                    label='MA5', color='orange', alpha=0.7)
            ax1.plot(df.index, df['close'].rolling(20).mean(), 
                    label='MA20', color='blue', alpha=0.7)
            ax1.plot(df.index, df['close'].rolling(60).mean(), 
                    label='MA60', color='red', alpha=0.7)
            ax1.legend(loc='upper left')
        
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.set_ylabel('价格')
        ax1.grid(True, alpha=0.3)
        
        # 绘制成交量
        if volume and ax2 is not None:
            colors = ['red' if df['close'].iloc[i] >= df['open'].iloc[i] 
                     else 'green' for i in range(len(df))]
            ax2.bar(df.index, df['volume'], color=colors, alpha=0.7)
            ax2.set_ylabel('成交量')
            ax2.grid(True, alpha=0.3)
        
        # 格式化x轴日期
        if ax2 is not None:
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        else:
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存至: {save_path}")
        
        plt.show()
    
    def _draw_candles(self, ax, df: pd.DataFrame) -> None:
        """绘制蜡烛图"""
        for i, (idx, row) in enumerate(df.iterrows()):
            open_price = row['open']
            close_price = row['close']
            high_price = row['high']
            low_price = row['low']
            
            # 确定颜色
            color = 'red' if close_price >= open_price else 'green'
            
            # 绘制实体
            height = abs(close_price - open_price)
            bottom = min(open_price, close_price)
            
            # 绘制影线
            ax.plot([idx, idx], [low_price, high_price], 
                   color=color, linewidth=1)
            
            # 绘制实体
            rect = Rectangle((mdates.date2num(idx) - 0.4, bottom), 
                           0.8, height, 
                           facecolor=color, edgecolor=color)
            ax.add_patch(rect)
    
    def plot_with_indicators(
        self,
        df: pd.DataFrame,
        indicators: List[str] = ['ma', 'macd', 'rsi', 'boll'],
        title: str = "技术分析图",
        save_path: Optional[str] = None
    ) -> None:
        """
        绘制带有技术指标的综合分析图
        
        Args:
            df: 股票数据
            indicators: 要显示的指标列表
            title: 图表标题
            save_path: 保存路径
        """
        # 创建子图
        n_plots = 1 + len([i for i in indicators if i != 'ma'])
        fig, axes = plt.subplots(n_plots, 1, figsize=(16, 4 * n_plots), 
                                sharex=True)
        
        if n_plots == 1:
            axes = [axes]
        
        # 主图: K线和MA
        ax_main = axes[0]
        self._draw_candles(ax_main, df)
        
        analyzer = TechnicalAnalyzer(df)
        
        # 添加移动平均线
        if 'ma' in indicators:
            ma5 = analyzer.ma(5)
            ma10 = analyzer.ma(10)
            ma20 = analyzer.ma(20)
            ma60 = analyzer.ma(60)
            
            ax_main.plot(df.index, ma5, label='MA5', color='orange', alpha=0.8)
            ax_main.plot(df.index, ma10, label='MA10', color='green', alpha=0.8)
            ax_main.plot(df.index, ma20, label='MA20', color='blue', alpha=0.8)
            ax_main.plot(df.index, ma60, label='MA60', color='red', alpha=0.8)
        
        # 添加布林带
        if 'boll' in indicators:
            boll = analyzer.boll()
            ax_main.plot(df.index, boll['upper'], label='BOLL Upper', 
                        color='purple', linestyle='--', alpha=0.7)
            ax_main.plot(df.index, boll['middle'], label='BOLL Middle', 
                        color='gray', linestyle='--', alpha=0.7)
            ax_main.plot(df.index, boll['lower'], label='BOLL Lower', 
                        color='purple', linestyle='--', alpha=0.7)
            ax_main.fill_between(df.index, boll['upper'], boll['lower'], 
                               alpha=0.1, color='gray')
        
        ax_main.set_title(title, fontsize=14, fontweight='bold')
        ax_main.set_ylabel('价格')
        ax_main.legend(loc='upper left')
        ax_main.grid(True, alpha=0.3)
        
        plot_idx = 1
        
        # MACD
        if 'macd' in indicators and plot_idx < len(axes):
            macd_data = analyzer.macd()
            ax_macd = axes[plot_idx]
            
            ax_macd.plot(df.index, macd_data['macd'], 
                        label='MACD', color='blue', alpha=0.8)
            ax_macd.plot(df.index, macd_data['signal'], 
                        label='Signal', color='red', alpha=0.8)
            ax_macd.bar(df.index, macd_data['histogram'], 
                       color=['red' if x > 0 else 'green' for x in macd_data['histogram']], 
                       alpha=0.5, label='Histogram')
            ax_macd.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax_macd.set_ylabel('MACD')
            ax_macd.legend(loc='upper left')
            ax_macd.grid(True, alpha=0.3)
            plot_idx += 1
        
        # RSI
        if 'rsi' in indicators and plot_idx < len(axes):
            rsi = analyzer.rsi()
            ax_rsi = axes[plot_idx]
            
            ax_rsi.plot(df.index, rsi, label='RSI', color='purple', alpha=0.8)
            ax_rsi.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Overbought')
            ax_rsi.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Oversold')
            ax_rsi.fill_between(df.index, 30, 70, alpha=0.1, color='gray')
            ax_rsi.set_ylabel('RSI')
            ax_rsi.set_ylim(0, 100)
            ax_rsi.legend(loc='upper left')
            ax_rsi.grid(True, alpha=0.3)
            plot_idx += 1
        
        # KDJ
        if 'kdj' in indicators and plot_idx < len(axes):
            kdj = analyzer.kdj()
            ax_kdj = axes[plot_idx]
            
            ax_kdj.plot(df.index, kdj['K'], label='K', color='blue', alpha=0.8)
            ax_kdj.plot(df.index, kdj['D'], label='D', color='orange', alpha=0.8)
            ax_kdj.plot(df.index, kdj['J'], label='J', color='purple', alpha=0.8)
            ax_kdj.axhline(y=80, color='red', linestyle='--', alpha=0.7)
            ax_kdj.axhline(y=20, color='green', linestyle='--', alpha=0.7)
            ax_kdj.set_ylabel('KDJ')
            ax_kdj.legend(loc='upper left')
            ax_kdj.grid(True, alpha=0.3)
            plot_idx += 1
        
        # 成交量
        if 'volume' in indicators and plot_idx < len(axes):
            vol_ma = analyzer.volume_ma(20)
            ax_vol = axes[plot_idx]
            
            colors = ['red' if df['close'].iloc[i] >= df['open'].iloc[i] 
                     else 'green' for i in range(len(df))]
            ax_vol.bar(df.index, df['volume'], color=colors, alpha=0.7)
            ax_vol.plot(df.index, vol_ma, label='Vol MA20', color='orange')
            ax_vol.set_ylabel('成交量')
            ax_vol.legend(loc='upper left')
            ax_vol.grid(True, alpha=0.3)
        
        # 格式化x轴
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存至: {save_path}")
        
        plt.show()
    
    def plot_correlation(
        self,
        data_dict: Dict[str, pd.DataFrame],
        save_path: Optional[str] = None
    ) -> None:
        """
        绘制多只股票的相关性热力图
        
        Args:
            data_dict: 股票代码和数据的字典
            save_path: 保存路径
        """
        # 提取收盘价
        close_prices = pd.DataFrame()
        for code, df in data_dict.items():
            close_prices[code] = df['close']
        
        # 计算相关性
        corr = close_prices.corr()
        
        # 绘制热力图
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
        
        # 设置刻度
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha='right')
        ax.set_yticklabels(corr.columns)
        
        # 添加数值标签
        for i in range(len(corr.columns)):
            for j in range(len(corr.columns)):
                text = ax.text(j, i, f'{corr.iloc[i, j]:.2f}',
                             ha="center", va="center", color="black")
        
        ax.set_title('股票价格相关性矩阵', fontsize=14, fontweight='bold')
        fig.colorbar(im, ax=ax)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存至: {save_path}")
        
        plt.show()
    
    def plot_performance_comparison(
        self,
        data_dict: Dict[str, pd.DataFrame],
        normalize: bool = True,
        save_path: Optional[str] = None
    ) -> None:
        """
        绘制多只股票收益对比图
        
        Args:
            data_dict: 股票代码和数据的字典
            normalize: 是否归一化
            save_path: 保存路径
        """
        fig, ax = plt.subplots(figsize=(14, 7))
        
        for code, df in data_dict.items():
            prices = df['close']
            
            if normalize:
                # 归一化到起始日为100
                normalized_prices = prices / prices.iloc[0] * 100
                ax.plot(df.index, normalized_prices, label=code, alpha=0.8, linewidth=2)
                ax.set_ylabel('归一化价格 (起始日=100)')
            else:
                ax.plot(df.index, prices, label=code, alpha=0.8, linewidth=2)
                ax.set_ylabel('价格')
        
        ax.set_title('股票收益对比', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存至: {save_path}")
        
        plt.show()
    
    def plot_distribution(
        self,
        df: pd.DataFrame,
        column: str = 'pct_change',
        bins: int = 50,
        title: str = None,
        save_path: Optional[str] = None
    ) -> None:
        """
        绘制收益率分布直方图
        
        Args:
            df: 股票数据
            column: 要分析的列
            bins: 直方图柱数
            title: 图表标题
            save_path: 保存路径
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        data = df[column].dropna()
        
        # 直方图
        ax1.hist(data, bins=bins, alpha=0.7, color='steelblue', edgecolor='black')
        ax1.axvline(data.mean(), color='red', linestyle='--', linewidth=2, label=f'均值: {data.mean():.2f}')
        ax1.axvline(data.median(), color='green', linestyle='--', linewidth=2, label=f'中位数: {data.median():.2f}')
        ax1.set_xlabel('收益率 (%)')
        ax1.set_ylabel('频数')
        ax1.set_title(title or f'{column} 分布')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 箱线图
        ax2.boxplot(data, vert=True)
        ax2.set_ylabel('收益率 (%)')
        ax2.set_title(f'{column} 箱线图')
        ax2.grid(True, alpha=0.3)
        
        # 添加统计信息
        stats_text = f"""
        统计信息:
        均值: {data.mean():.2f}
        标准差: {data.std():.2f}
        最大值: {data.max():.2f}
        最小值: {data.min():.2f}
        偏度: {data.skew():.2f}
        峰度: {data.kurtosis():.2f}
        """
        ax2.text(1.1, data.median(), stats_text, verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存至: {save_path}")
        
        plt.show()
    
    def plot_drawdown(
        self,
        df: pd.DataFrame,
        title: str = "回撤分析",
        save_path: Optional[str] = None
    ) -> None:
        """
        绘制回撤分析图
        
        Args:
            df: 股票数据
            title: 图表标题
            save_path: 保存路径
        """
        # 计算累计收益和回撤
        cumulative = (1 + df['pct_change'] / 100).cumprod()
        peak = cumulative.expanding().max()
        drawdown = (cumulative - peak) / peak * 100
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        
        # 累计收益
        ax1.plot(df.index, cumulative, label='累计收益', color='blue', linewidth=2)
        ax1.fill_between(df.index, 1, cumulative, alpha=0.3, 
                        color=['green' if x >= 1 else 'red' for x in cumulative])
        ax1.axhline(y=1, color='black', linestyle='--', linewidth=1)
        ax1.set_ylabel('累计收益倍数')
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 回撤
        ax2.fill_between(df.index, drawdown, 0, alpha=0.5, color='red')
        ax2.plot(df.index, drawdown, color='darkred', linewidth=2)
        ax2.set_ylabel('回撤 (%)')
        ax2.set_xlabel('日期')
        ax2.grid(True, alpha=0.3)
        
        # 格式化x轴
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # 添加统计信息
        max_drawdown = drawdown.min()
        ax2.text(0.02, 0.05, f'最大回撤: {max_drawdown:.2f}%', 
                transform=ax2.transAxes, fontsize=12,
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存至: {save_path}")
        
        plt.show()


# 便捷函数
def plot_stock_analysis(df: pd.DataFrame, title: str = "股票分析") -> None:
    """
    快速绘制股票分析图的便捷函数
    
    Args:
        df: 股票数据
        title: 图表标题
    """
    visualizer = StockVisualizer()
    visualizer.plot_with_indicators(df, title=title)


def compare_stocks(data_dict: Dict[str, pd.DataFrame]) -> None:
    """
    比较多只股票收益的便捷函数
    
    Args:
        data_dict: 股票代码和数据的字典
    """
    visualizer = StockVisualizer()
    visualizer.plot_performance_comparison(data_dict)