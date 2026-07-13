"""
第二步：定时获取全市场股票 + ETF基金实时行情
每60秒自动刷新一次，存入数据库
"""

import akshare as ak
import pandas as pd
import sqlite3
import os
import time
from datetime import datetime
import warnings
import socket
warnings.filterwarnings('ignore')

# ===== 删除旧的 update_log 表（解决列不匹配问题）=====
print("=" * 60)
print("🚀 启动实时行情更新程序...")
print("=" * 60)

conn = sqlite3.connect('stock_data.db')
try:
    conn.execute("DROP TABLE IF EXISTS update_log")
    print("✅ 已清理旧的日志表")
except:
    pass
conn.close()

# 数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'stock_data.db')

# 更新计数器
update_count = 0


def fetch_all_realtime():
    """
    获取所有股票和ETF基金的实时行情
    """
    global update_count
    update_count += 1
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n" + "-" * 50)
    print(f"📡 第 {update_count} 次更新 - {current_time}")
    print("-" * 50)
    
    # ----- 1. 获取股票实时行情 -----
    print("   [1/2] 获取股票实时行情...")
    stock_realtime = None
    try:
        socket.setdefaulttimeout(15)
        stock_realtime = ak.stock_zh_a_spot()
        print(f"      ✅ 股票数据: {len(stock_realtime)} 只")
    except Exception as e:
        print(f"      ⚠️ 股票获取超时或失败: {str(e)[:30]}...")
    
    # ----- 2. 获取ETF基金实时行情 -----
    print("   [2/2] 获取ETF基金实时行情...")
    etf_realtime = None
    try:
        socket.setdefaulttimeout(15)
        etf_realtime = ak.fund_etf_spot_em()
        print(f"      ✅ ETF数据: {len(etf_realtime)} 只")
    except Exception as e:
        print(f"      ⚠️ ETF获取超时或失败: {str(e)[:30]}...")
    
    # ----- 3. 存入数据库 -----
    conn = sqlite3.connect(db_path)
    
    if stock_realtime is not None and not stock_realtime.empty:
        stock_realtime.to_sql('stock_realtime', conn, if_exists='replace', index=False)
        print("      💾 股票数据已存入数据库")
    
    if etf_realtime is not None and not etf_realtime.empty:
        etf_realtime.to_sql('etf_realtime', conn, if_exists='replace', index=False)
        print("      💾 ETF数据已存入数据库")
    
    # 记录更新日志
    stock_count = len(stock_realtime) if stock_realtime is not None else 0
    etf_count = len(etf_realtime) if etf_realtime is not None else 0
    
    update_log = pd.DataFrame({
        'update_time': [current_time],
        'stock_count': [stock_count],
        'etf_count': [etf_count]
    })
    update_log.to_sql('update_log', conn, if_exists='append', index=False)
    
    conn.close()
    print(f"      ✅ 本次更新完成 (股票:{stock_count}, ETF:{etf_count})")
    print("-" * 50)


def get_stock_count():
    """获取数据库中已有的股票数量"""
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql("SELECT COUNT(*) as count FROM stock_list", conn)
        conn.close()
        return df['count'].iloc[0]
    except:
        return 0


# ========== 主程序 ==========
print("\n📊 检查数据库...")
count = get_stock_count()
if count == 0:
    print("⚠️ 数据库中暂无股票列表，请先运行 step1_get_stock_etf.py")
    print("程序将在5秒后退出...")
    time.sleep(5)
    exit()
else:
    print(f"✅ 数据库中有 {count} 只股票 + ETF基金")

print("\n" + "=" * 60)
print("⏰ 程序已启动，每60秒自动更新一次")
print("   按 Ctrl + C 可停止程序")
print("=" * 60)

# 立即执行一次更新
fetch_all_realtime()

# 定时循环执行（每60秒）
try:
    while True:
        time.sleep(60)
        fetch_all_realtime()
except KeyboardInterrupt:
    print("\n\n" + "=" * 60)
    print(f"🛑 程序已停止（共执行 {update_count} 次更新）")
    print("=" * 60)