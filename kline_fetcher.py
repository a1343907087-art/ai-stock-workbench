"""
K线数据获取模块
用于获取单只股票的历史K线数据
"""

import akshare as ak
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta

db_path = os.path.join(os.path.dirname(__file__), 'stock_data.db')


def get_stock_kline(symbol, start_date=None, end_date=None, adjust="qfq"):
    """
    获取单只股票的K线数据
    
    参数:
        symbol: 股票代码（如 '000001'）
        start_date: 开始日期（格式 '2025-01-01'）
        end_date: 结束日期（格式 '2025-12-31'）
        adjust: 复权类型（'qfq'前复权, 'hfq'后复权, ''不复权）
    
    返回:
        DataFrame: 包含日期、开盘、最高、最低、收盘、成交量
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    # 转换日期格式
    start_date = start_date.replace('-', '')
    end_date = end_date.replace('-', '')
    
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        # 重命名列
        df.rename(columns={
            '日期': 'trade_date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change',
            '换手率': 'turnover'
        }, inplace=True)
        
        return df
    except Exception as e:
        print(f"获取K线数据失败: {e}")
        return pd.DataFrame()


def get_etf_kline(symbol, start_date=None, end_date=None):
    """获取ETF基金的K线数据"""
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    start_date = start_date.replace('-', '')
    end_date = end_date.replace('-', '')
    
    try:
        # ETF基金用基金代码获取数据，加上 .SH 或 .SZ 后缀
        # 根据代码判断交易所
        if symbol.startswith('51') or symbol.startswith('56'):
            code = f"{symbol}.SH"
        elif symbol.startswith('15'):
            code = f"{symbol}.SZ"
        else:
            code = f"{symbol}.SZ"
        
        df = ak.fund_etf_hist_em(symbol=code, period="daily", 
                                  start_date=start_date, end_date=end_date, adjust="qfq")
        
        df.rename(columns={
            '日期': 'trade_date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount'
        }, inplace=True)
        
        return df
    except Exception as e:
        print(f"获取ETF K线数据失败: {e}")
        return pd.DataFrame()


def save_kline_to_db(symbol, df, data_type='stock'):
    """将K线数据存入数据库"""
    if df.empty:
        print(f"⚠️ {symbol} 没有数据可存储")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        table_name = f"kline_{data_type}_{symbol}"
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()
        print(f"✅ {symbol} K线数据已存入数据库 ({len(df)} 条)")
        return True
    except Exception as e:
        print(f"❌ 存储失败: {e}")
        return False


# 测试函数
if __name__ == "__main__":
    print("=" * 50)
    print("🧪 测试K线数据获取")
    print("=" * 50)
    
    # 测试获取平安银行的K线数据
    print("\n📡 获取平安银行(000001)的K线数据...")
    df = get_stock_kline('000001', start_date='2025-01-01', end_date='2025-07-13')
    
    if not df.empty:
        print(f"✅ 获取成功! 共 {len(df)} 条数据")
        print("\n前5行数据:")
        print(df.head())
        print("\n数据列:", df.columns.tolist())
        
        # 保存到数据库
        save_kline_to_db('000001', df, 'stock')
    else:
        print("❌ 获取失败")