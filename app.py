#!/usr/bin/env python3
"""
A股分析系统 - Web界面 (Flask)
"""

import io
import base64
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file
from flask_bootstrap import Bootstrap
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt

from src import (
    BaoStockDataFetcher,
    TechnicalAnalyzer,
    StockVisualizer,
    MACDStrategy,
    RSIStrategy,
    GoldenCrossStrategy,
    VolumeBreakoutStrategy,
    MultiIndicatorStrategy,
    FundamentalStrategy
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stock-analyzer-2024'
Bootstrap(app)

# 全局数据获取器 - 使用BaoStockDataFetcher
fetcher = BaoStockDataFetcher()
visualizer = StockVisualizer()


def fig_to_base64(fig):
    """将matplotlib图表转换为base64字符串"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return image_base64


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/stock_list')
def api_stock_list():
    """获取股票列表API"""
    try:
        stocks = fetcher.get_stock_list()
        # 只返回部分字段，避免数据过大
        stocks = stocks.head(500)  # 限制返回数量
        data = stocks.to_dict(orient='records')
        return jsonify({
            'success': True,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/stock_info/<code>')
def api_stock_info(code):
    """获取单只股票信息"""
    try:
        # 实时行情
        spot = fetcher.get_stock_spot(code)
        
        # 历史数据
        df = fetcher.get_historical_data(code, days=30)
        
        if df.empty:
            return jsonify({'success': False, 'error': '未找到股票数据'})
        
        # 最近5天数据
        recent = df.tail(5)[['close', 'open', 'high', 'low', 'volume', 'pct_change']]
        recent_dict = recent.reset_index().to_dict(orient='records')
        for item in recent_dict:
            item['date'] = item['date'].strftime('%Y-%m-%d') if hasattr(item['date'], 'strftime') else str(item['date'])
        
        return jsonify({
            'success': True,
            'code': code,
            'spot': spot,
            'recent_data': recent_dict,
            'stats': {
                'max_30d': float(df['high'].max()),
                'min_30d': float(df['low'].min()),
                'avg_volume': float(df['volume'].mean()),
                'total_change_5d': float(df['pct_change'].tail(5).sum())
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/technical_analysis/<code>')
def api_technical_analysis(code):
    """技术分析API"""
    try:
        days = request.args.get('days', 60, type=int)
        df = fetcher.get_historical_data(code, days=days)
        
        if df.empty:
            return jsonify({'success': False, 'error': '未找到股票数据'})
        
        analyzer = TechnicalAnalyzer(df)
        signals = analyzer.get_latest_signals()
        
        # 转换numpy类型为Python类型
        def convert_value(v):
            if hasattr(v, 'item'):
                return v.item()
            return v
        
        signals = {k: convert_value(v) for k, v in signals.items()}
        
        return jsonify({
            'success': True,
            'code': code,
            'signals': signals
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/chart/<code>')
def api_chart(code):
    """生成图表API"""
    try:
        days = request.args.get('days', 90, type=int)
        chart_type = request.args.get('type', 'technical')  # technical, kline, volume
        
        df = fetcher.get_historical_data(code, days=days)
        
        if df.empty:
            return jsonify({'success': False, 'error': '未找到股票数据'})
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if chart_type == 'kline':
            # 简化版K线图
            ax.plot(df.index, df['close'], label='收盘价', linewidth=2)
            ax.fill_between(df.index, df['low'], df['high'], alpha=0.3, label='价格区间')
            ax.set_title(f'{code} 价格走势')
            
        elif chart_type == 'volume':
            # 成交量图
            colors = ['red' if df['close'].iloc[i] >= df['open'].iloc[i] 
                     else 'green' for i in range(len(df))]
            ax.bar(df.index, df['volume'], color=colors, alpha=0.7)
            ax.set_title(f'{code} 成交量')
            
        else:  # technical
            # 价格+均线
            ax.plot(df.index, df['close'], label='收盘价', linewidth=2)
            
            # 计算均线
            analyzer = TechnicalAnalyzer(df)
            ma5 = analyzer.ma(5)
            ma10 = analyzer.ma(10)
            ma20 = analyzer.ma(20)
            
            ax.plot(df.index, ma5, label='MA5', alpha=0.8)
            ax.plot(df.index, ma10, label='MA10', alpha=0.8)
            ax.plot(df.index, ma20, label='MA20', alpha=0.8)
            
            ax.set_title(f'{code} 技术分析')
            ax.legend()
        
        ax.set_xlabel('日期')
        ax.set_ylabel('价格/成交量')
        ax.grid(True, alpha=0.3)
        
        # 旋转x轴标签
        for label in ax.xaxis.get_ticklabels():
            label.set_rotation(45)
        
        plt.tight_layout()
        
        # 转换为base64
        img_base64 = fig_to_base64(fig)
        
        return jsonify({
            'success': True,
            'chart': img_base64
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/screening', methods=['POST'])
def api_screening():
    """选股策略API"""
    try:
        data = request.get_json()
        strategy_type = data.get('strategy', 'multi')
        limit = data.get('limit', 100)
        
        # 获取股票列表
        stocks = fetcher.get_stock_list()
        if limit > 0:
            stocks = stocks.head(limit)
        
        result = []
        strategy_name = ""
        
        if strategy_type == 'macd':
            strategy = MACDStrategy()
            result_df = strategy.filter(stocks)
            strategy_name = "MACD金叉策略"
            
        elif strategy_type == 'rsi':
            threshold = data.get('threshold', 30)
            strategy = RSIStrategy(threshold)
            result_df = strategy.filter(stocks)
            strategy_name = f"RSI超卖策略(阈值{threshold})"
            
        elif strategy_type == 'golden_cross':
            short = data.get('short_ma', 5)
            long = data.get('long_ma', 20)
            strategy = GoldenCrossStrategy(short, long)
            result_df = strategy.filter(stocks)
            strategy_name = f"均线金叉策略(MA{short}/MA{long})"
            
        elif strategy_type == 'volume':
            ratio = data.get('ratio', 2.0)
            strategy = VolumeBreakoutStrategy(ratio)
            result_df = strategy.filter(stocks)
            strategy_name = f"放量突破策略(倍数{ratio})"
            
        elif strategy_type == 'fundamental':
            max_pe = data.get('max_pe', 30)
            max_pb = data.get('max_pb', 3)
            min_cap = data.get('min_cap', 100)
            
            strategy = FundamentalStrategy()
            result_df = strategy.filter(
                stocks,
                max_pe=max_pe if max_pe > 0 else None,
                max_pb=max_pb if max_pb > 0 else None,
                min_market_cap=min_cap if min_cap > 0 else None
            )
            strategy_name = f"基本面选股(PE<{max_pe}, PB<{max_pb})"
            
        else:  # multi
            strategy = MultiIndicatorStrategy()
            result_df = strategy.filter(stocks)
            strategy_name = "多指标综合策略"
        
        # 转换为字典
        if not result_df.empty:
            result = result_df.head(50).to_dict(orient='records')
        
        return jsonify({
            'success': True,
            'strategy': strategy_name,
            'count': len(result),
            'data': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/sectors')
def api_sectors():
    """行业板块数据"""
    try:
        sectors = fetcher.get_industry_ranking()
        if not sectors.empty:
            data = sectors.head(50).to_dict(orient='records')
            return jsonify({
                'success': True,
                'count': len(data),
                'data': data
            })
        return jsonify({'success': False, 'error': '获取失败'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/stock/<code>')
def stock_detail(code):
    """股票详情页面"""
    return render_template('stock_detail.html', code=code)


@app.route('/analysis')
def analysis_page():
    """技术分析页面"""
    return render_template('analysis.html')


@app.route('/screening')
def screening_page():
    """选股策略页面"""
    return render_template('screening.html')


@app.route('/sectors')
def sectors_page():
    """行业板块页面"""
    return render_template('sectors.html')


@app.route('/compare')
def compare_page():
    """股票对比页面"""
    return render_template('compare.html')


if __name__ == '__main__':
    print("=" * 60)
    print("A股分析系统 - Web服务器")
    print("=" * 60)
    print("访问地址: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)