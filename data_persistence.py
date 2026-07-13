"""
第八步：数据持久化模块
自动存档历史数据，防止数据丢失
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta
import json

db_path = os.path.join(os.path.dirname(__file__), 'stock_data.db')
ARCHIVE_DIR = 'data_archive'

# 确保存档目录存在
if not os.path.exists(ARCHIVE_DIR):
    os.makedirs(ARCHIVE_DIR)


def archive_realtime_data():
    """
    将当前实时数据存档到CSV文件
    每天自动保存一份
    """
    try:
        conn = sqlite3.connect(db_path)
        
        # 获取股票实时数据
        try:
            stock_df = pd.read_sql("SELECT * FROM stock_realtime", conn)
        except:
            stock_df = pd.DataFrame()
        
        # 获取ETF实时数据
        try:
            etf_df = pd.read_sql("SELECT * FROM etf_realtime", conn)
        except:
            etf_df = pd.DataFrame()
        
        conn.close()
        
        # 生成文件名（按日期）
        today = datetime.now().strftime('%Y%m%d')
        
        # 保存股票数据
        if not stock_df.empty:
            stock_file = os.path.join(ARCHIVE_DIR, f'stock_{today}.csv')
            stock_df.to_csv(stock_file, index=False, encoding='utf-8-sig')
            print(f"✅ 股票数据已存档: {stock_file}")
        
        # 保存ETF数据
        if not etf_df.empty:
            etf_file = os.path.join(ARCHIVE_DIR, f'etf_{today}.csv')
            etf_df.to_csv(etf_file, index=False, encoding='utf-8-sig')
            print(f"✅ ETF数据已存档: {etf_file}")
        
        return True
    except Exception as e:
        print(f"❌ 数据存档失败: {e}")
        return False


def load_historical_data(date_str=None):
    """
    加载历史数据
    
    参数:
        date_str: 日期字符串（格式 '20250101'），不指定则加载最新
    """
    if date_str is None:
        # 获取最近的数据文件
        files = os.listdir(ARCHIVE_DIR)
        stock_files = [f for f in files if f.startswith('stock_') and f.endswith('.csv')]
        if not stock_files:
            return None
        stock_files.sort(reverse=True)
        date_str = stock_files[0].replace('stock_', '').replace('.csv', '')
    
    try:
        stock_file = os.path.join(ARCHIVE_DIR, f'stock_{date_str}.csv')
        etf_file = os.path.join(ARCHIVE_DIR, f'etf_{date_str}.csv')
        
        stock_df = pd.read_csv(stock_file) if os.path.exists(stock_file) else pd.DataFrame()
        etf_df = pd.read_csv(etf_file) if os.path.exists(etf_file) else pd.DataFrame()
        
        return {
            'stock': stock_df,
            'etf': etf_df,
            'date': date_str
        }
    except Exception as e:
        print(f"❌ 加载历史数据失败: {e}")
        return None


def clean_old_archives(days=30):
    """
    清理旧存档，只保留最近N天的数据
    
    参数:
        days: 保留天数（默认30天）
    """
    try:
        cutoff = datetime.now() - timedelta(days=days)
        files = os.listdir(ARCHIVE_DIR)
        deleted = 0
        
        for f in files:
            if f.endswith('.csv'):
                file_path = os.path.join(ARCHIVE_DIR, f)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff:
                    os.remove(file_path)
                    deleted += 1
        
        print(f"✅ 已清理 {deleted} 个旧文件")
        return deleted
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        return 0


def get_archive_stats():
    """获取存档统计信息"""
    files = os.listdir(ARCHIVE_DIR)
    stock_files = [f for f in files if f.startswith('stock_') and f.endswith('.csv')]
    etf_files = [f for f in files if f.startswith('etf_') and f.endswith('.csv')]
    
    return {
        'total_files': len(files),
        'stock_archives': len(stock_files),
        'etf_archives': len(etf_files),
        'latest': stock_files[0] if stock_files else None
    }


# 测试函数
if __name__ == "__main__":
    print("=" * 50)
    print("📦 测试数据持久化模块")
    print("=" * 50)
    
    # 显示存档统计
    stats = get_archive_stats()
    print(f"\n📊 存档统计:")
    print(f"  总文件数: {stats['total_files']}")
    print(f"  股票存档: {stats['stock_archives']}")
    print(f"  ETF存档: {stats['etf_archives']}")
    print(f"  最新存档: {stats['latest']}")
    
    # 执行一次存档
    print("\n📡 执行数据存档...")
    archive_realtime_data()
    
    # 清理旧文件（保留30天）
    print("\n🧹 清理旧文件...")
    clean_old_archives(days=30)
    
    print("\n✅ 数据持久化模块测试完成！")