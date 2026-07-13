"""
第一步：获取A股所有股票 + ETF基金列表，存入数据库
"""

import akshare as ak
import pandas as pd
import sqlite3
import os
import time

print("=" * 60)
print("🚀 开始获取A股股票 + ETF基金列表...")
print("=" * 60)

# 数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'stock_data.db')
conn = sqlite3.connect(db_path)

# ========== 1. 获取股票列表 ==========
print("\n📡 [1/3] 正在获取股票列表...")
try:
    stock_list = ak.stock_info_a_code_name()
    stock_list['类型'] = '股票'
    print(f"   ✅ 股票获取成功: {len(stock_list)} 只")
except Exception as e:
    print(f"   ❌ 股票获取失败: {e}")
    print("   ⚠️ 尝试备用数据源...")
    try:
        stock_list = ak.stock_zh_a_spot()
        stock_list = stock_list[['代码', '名称']]
        stock_list['类型'] = '股票'
        print(f"   ✅ 备用源成功: {len(stock_list)} 只")
    except Exception as e2:
        print(f"   ❌ 备用源也失败: {e2}")
        stock_list = pd.DataFrame()

# ========== 2. 获取ETF基金列表 ==========
print("\n📡 [2/3] 正在获取ETF基金列表...")
try:
    # 获取所有ETF基金的实时行情（包含所有ETF）
    etf_list = ak.fund_etf_spot_em()
    # 只保留代码和名称
    etf_list = etf_list[['代码', '名称']]
    etf_list['类型'] = 'ETF基金'
    print(f"   ✅ ETF基金获取成功: {len(etf_list)} 只")
except Exception as e:
    print(f"   ❌ ETF基金获取失败: {e}")
    print("   ⚠️ 尝试备用数据源...")
    try:
        # 备用方案：从基金列表中筛选ETF
        fund_all = ak.fund_name_em()
        # ETF基金名称通常包含"ETF"字样
        etf_list = fund_all[fund_all['基金简称'].str.contains('ETF', case=False)]
        etf_list = etf_list[['基金代码', '基金简称']]
        etf_list.columns = ['代码', '名称']
        etf_list['类型'] = 'ETF基金'
        print(f"   ✅ 备用源成功: {len(etf_list)} 只")
    except Exception as e2:
        print(f"   ❌ 备用源也失败: {e2}")
        etf_list = pd.DataFrame()

# ========== 3. 合并数据 ==========
print("\n📊 [3/3] 合并数据...")

# 检查数据是否为空
if stock_list.empty and etf_list.empty:
    print("❌ 所有数据获取失败，程序退出")
    conn.close()
    exit()

# 合并
all_list = pd.concat([stock_list, etf_list], ignore_index=True)
print(f"   ✅ 合并完成")
print(f"   📊 总计: {len(all_list)} 条记录")
print(f"      - 股票: {len(stock_list)} 只")
print(f"      - ETF基金: {len(etf_list)} 只")

# ========== 4. 存入数据库 ==========
print("\n💾 正在存入数据库...")

# 存入合并表
all_list.to_sql('all_list', conn, if_exists='replace', index=False)

# 分别存入分类表
if not stock_list.empty:
    stock_list.to_sql('stock_list', conn, if_exists='replace', index=False)
if not etf_list.empty:
    etf_list.to_sql('etf_list', conn, if_exists='replace', index=False)

conn.close()
print(f"   ✅ 数据已存入数据库: {db_path}")

# ========== 5. 验证数据 ==========
print("\n🔍 验证数据库内容...")
conn = sqlite3.connect(db_path)

print("\n📌 股票示例（前5只）：")
df_stock = pd.read_sql("SELECT * FROM stock_list LIMIT 5", conn)
print(df_stock.to_string(index=False))

print("\n📌 ETF基金示例（前5只）：")
df_etf = pd.read_sql("SELECT * FROM etf_list LIMIT 5", conn)
print(df_etf.to_string(index=False))

print("\n📌 合并列表统计：")
df_all = pd.read_sql("SELECT 类型, COUNT(*) as 数量 FROM all_list GROUP BY 类型", conn)
print(df_all.to_string(index=False))

conn.close()

print("\n" + "=" * 60)
print("🎉 第一步完成！")
print(f"📊 监控范围: {len(all_list)} 个标的（股票 + ETF基金）")
print("=" * 60)