import sqlite3
import pandas as pd

conn = sqlite3.connect('stock_data.db')

# 查看所有表
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
print("📋 数据库中的表：")
print(tables)

# 查看股票数据
try:
    df = pd.read_sql("SELECT * FROM stock_realtime LIMIT 5", conn)
    print("\n📊 股票数据（前5行）：")
    print(df[['代码', '名称', '最新价', '涨跌幅']])
except Exception as e:
    print(f"\n❌ 读取股票数据失败: {e}")

conn.close()