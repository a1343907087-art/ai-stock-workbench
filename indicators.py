"""
技术指标计算模块
包含 MACD、RSI、布林带、KDJ 等常用指标
"""

import pandas as pd
import numpy as np


def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    计算 MACD 指标
    
    参数:
        df: 包含 'close' 列的 DataFrame
        fast: 快线周期（默认12）
        slow: 慢线周期（默认26）
        signal: 信号线周期（默认9）
    
    返回:
        df: 添加了 MACD 相关列的 DataFrame
    """
    df = df.copy()
    
    # 计算指数移动平均
    df['ema_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
    
    # MACD 线 = 快线 - 慢线
    df['macd'] = df['ema_fast'] - df['ema_slow']
    
    # 信号线 = MACD 的 EMA
    df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
    
    # MACD 柱状图 = MACD - 信号线
    df['macd_histogram'] = df['macd'] - df['macd_signal']
    
    return df


def calculate_rsi(df, period=14):
    """
    计算 RSI（相对强弱指标）
    
    参数:
        df: 包含 'close' 列的 DataFrame
        period: 计算周期（默认14）
    
    返回:
        df: 添加了 'rsi' 列的 DataFrame
    """
    df = df.copy()
    
    # 计算价格变化
    delta = df['close'].diff()
    
    # 分离涨跌
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # 计算平均涨跌幅
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # 计算 RSI
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    return df


def calculate_bollinger_bands(df, period=20, std_dev=2):
    """
    计算布林带指标
    
    参数:
        df: 包含 'close' 列的 DataFrame
        period: 移动平均周期（默认20）
        std_dev: 标准差倍数（默认2）
    
    返回:
        df: 添加了布林带相关列的 DataFrame
    """
    df = df.copy()
    
    # 中轨 = 移动平均线
    df['bb_middle'] = df['close'].rolling(window=period).mean()
    
    # 标准差
    df['bb_std'] = df['close'].rolling(window=period).std()
    
    # 上轨 = 中轨 + 标准差 * 倍数
    df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * std_dev)
    
    # 下轨 = 中轨 - 标准差 * 倍数
    df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * std_dev)
    
    # 布林带宽度（波动率指标）
    df['bb_width'] = df['bb_upper'] - df['bb_lower']
    
    # 价格位置（0-1之间，0在下轨，1在上轨）
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    return df


def calculate_kdj(df, period=9, k_period=3, d_period=3):
    """
    计算 KDJ 指标
    
    参数:
        df: 包含 'high', 'low', 'close' 列的 DataFrame
        period: RSV 计算周期（默认9）
        k_period: K 线平滑周期（默认3）
        d_period: D 线平滑周期（默认3）
    
    返回:
        df: 添加了 KDJ 相关列的 DataFrame
    """
    df = df.copy()
    
    # 计算 RSV（未成熟随机值）
    low_min = df['low'].rolling(window=period).min()
    high_max = df['high'].rolling(window=period).max()
    df['rsv'] = (df['close'] - low_min) / (high_max - low_min) * 100
    
    # 计算 K 值
    df['kdj_k'] = df['rsv'].ewm(span=k_period, adjust=False).mean()
    
    # 计算 D 值
    df['kdj_d'] = df['kdj_k'].ewm(span=d_period, adjust=False).mean()
    
    # 计算 J 值 = 3K - 2D
    df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
    
    return df


def calculate_ma(df, periods=[5, 10, 20, 60]):
    """
    计算移动平均线
    
    参数:
        df: 包含 'close' 列的 DataFrame
        periods: 周期列表
    
    返回:
        df: 添加了 MA 列的 DataFrame
    """
    df = df.copy()
    for p in periods:
        df[f'ma_{p}'] = df['close'].rolling(window=p).mean()
    return df


def calculate_all_indicators(df):
    """
    一次性计算所有技术指标
    """
    if df.empty or len(df) < 20:
        return df
    
    df = df.copy()
    
    # 确保数据类型正确
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['high'] = pd.to_numeric(df['high'], errors='coerce')
    df['low'] = pd.to_numeric(df['low'], errors='coerce')
    df['open'] = pd.to_numeric(df['open'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    
    # 删除空值
    df = df.dropna(subset=['close', 'high', 'low'])
    
    if len(df) < 20:
        return df
    
    # 计算各类指标
    df = calculate_ma(df)
    df = calculate_macd(df)
    df = calculate_rsi(df)
    df = calculate_bollinger_bands(df)
    df = calculate_kdj(df)
    
    return df


def generate_signals(df):
    """
    根据技术指标生成买卖信号
    
    返回:
        df: 添加了 'signal' 列的 DataFrame（buy/sell/hold）
    """
    df = df.copy()
    
    if df.empty or 'rsi' not in df.columns:
        return df
    
    # 初始化信号列
    df['signal'] = 'hold'
    
    # 买入信号条件
    buy_conditions = (
        (df['rsi'] < 30) |  # RSI 超卖
        ((df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))) |  # MACD 金叉
        (df['close'] < df['bb_lower'])  # 价格低于布林带下轨
    )
    
    # 卖出信号条件
    sell_conditions = (
        (df['rsi'] > 70) |  # RSI 超买
        ((df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))) |  # MACD 死叉
        (df['close'] > df['bb_upper'])  # 价格高于布林带上轨
    )
    
    df.loc[buy_conditions, 'signal'] = 'buy'
    df.loc[sell_conditions, 'signal'] = 'sell'
    
    return df


def scan_stocks(stock_list, conn):
    """
    扫描股票列表，筛选出有交易信号的股票
    """
    results = []
    
    for code, name in stock_list:
        try:
            # 从数据库获取K线数据
            table_name = f'kline_stock_{code}'
            df = pd.read_sql(f"SELECT * FROM {table_name} ORDER BY trade_date DESC LIMIT 100", conn)
            
            if df.empty:
                continue
            
            df = calculate_all_indicators(df)
            df = generate_signals(df)
            
            # 获取最新信号
            latest = df.iloc[-1]
            
            if latest.get('signal') in ['buy', 'sell']:
                results.append({
                    '代码': code,
                    '名称': name,
                    '信号': latest['signal'],
                    '最新价': latest['close'],
                    '涨跌幅': latest.get('pct_change', 0),
                    'RSI': latest.get('rsi', 0),
                    'MACD': latest.get('macd', 0)
                })
        except Exception as e:
            # 跳过没有K线数据的股票
            continue
    
    return results


# 测试函数
if __name__ == "__main__":
    print("=" * 50)
    print("🧪 测试技术指标计算")
    print("=" * 50)
    
    # 生成模拟数据
    np.random.seed(42)
    dates = pd.date_range(start='2025-01-01', end='2025-07-13', freq='D')
    price = 10.0
    prices = []
    for i in range(len(dates)):
        price = price * (1 + np.random.normal(0, 0.015))
        prices.append(round(price, 2))
    
    df = pd.DataFrame({
        'trade_date': dates,
        'open': prices,
        'high': [p * 1.02 for p in prices],
        'low': [p * 0.98 for p in prices],
        'close': [p * 1.01 for p in prices],
        'volume': np.random.randint(1000000, 5000000, len(dates))
    })
    
    # 计算指标
    df = calculate_all_indicators(df)
    df = generate_signals(df)
    
    print("\n📊 技术指标计算结果（最近5天）：")
    cols = ['trade_date', 'close', 'ma_5', 'ma_20', 'rsi', 'macd', 'bb_upper', 'bb_lower', 'kdj_k', 'kdj_d', 'signal']
    print(df[cols].tail(5).to_string(index=False))
    
    print("\n✅ 技术指标模块测试完成！")