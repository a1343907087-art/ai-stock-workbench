"""
第十步：数据备份和系统维护模块
自动备份数据库、日志记录、健康检查
"""

import os
import shutil
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import logging

# ========== 配置 ==========
BACKUP_DIR = 'backups'
LOG_DIR = 'logs'
DB_PATH = 'stock_data.db'
MAX_BACKUPS = 30  # 最多保留30个备份
MAX_LOGS = 20     # 最多保留20个日志文件

# 确保目录存在
for dir_name in [BACKUP_DIR, LOG_DIR]:
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

# ========== 日志配置 ==========
def setup_logging():
    """配置日志系统"""
    log_file = os.path.join(LOG_DIR, f'system_{datetime.now().strftime("%Y%m%d")}.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到终端
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


# ========== 数据库备份 ==========
def backup_database():
    """
    备份数据库到 backups/ 目录
    文件名格式：stock_data_20250714_143022.db
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f'stock_data_{timestamp}.db')
        
        # 如果数据库不存在，直接返回
        if not os.path.exists(DB_PATH):
            logger.warning(f"数据库文件 {DB_PATH} 不存在，跳过备份")
            return False
        
        # 复制文件
        shutil.copy2(DB_PATH, backup_file)
        logger.info(f"✅ 数据库备份成功: {backup_file}")
        
        # 清理旧备份
        clean_old_backups()
        
        return backup_file
    except Exception as e:
        logger.error(f"❌ 数据库备份失败: {e}")
        return False


def clean_old_backups():
    """清理多余的备份文件，只保留最新的 MAX_BACKUPS 个"""
    try:
        files = [f for f in os.listdir(BACKUP_DIR) if f.startswith('stock_data_') and f.endswith('.db')]
        files.sort(reverse=True)  # 最新的在前
        
        if len(files) > MAX_BACKUPS:
            for f in files[MAX_BACKUPS:]:
                os.remove(os.path.join(BACKUP_DIR, f))
                logger.info(f"   🗑️ 已删除旧备份: {f}")
        
        return len(files)
    except Exception as e:
        logger.error(f"清理备份失败: {e}")
        return 0


def list_backups():
    """列出所有备份文件"""
    files = [f for f in os.listdir(BACKUP_DIR) if f.startswith('stock_data_') and f.endswith('.db')]
    files.sort(reverse=True)
    
    result = []
    for f in files:
        file_path = os.path.join(BACKUP_DIR, f)
        size = os.path.getsize(file_path) / 1024  # KB
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        result.append({
            'name': f,
            'size': f"{size:.1f} KB",
            'time': mtime.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return result


def restore_backup(backup_name):
    """
    从备份恢复数据库
    
    参数:
        backup_name: 备份文件名（如 'stock_data_20250714_143022.db'）
    """
    try:
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        if not os.path.exists(backup_path):
            logger.error(f"备份文件 {backup_name} 不存在")
            return False
        
        # 先备份当前数据库（以防万一）
        if os.path.exists(DB_PATH):
            backup_database()
        
        # 恢复
        shutil.copy2(backup_path, DB_PATH)
        logger.info(f"✅ 数据库已从 {backup_name} 恢复")
        return True
    except Exception as e:
        logger.error(f"❌ 恢复失败: {e}")
        return False


# ========== 导出数据 ==========
def export_data_to_excel():
    """导出所有数据到 Excel 文件"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # 获取所有表名
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_file = os.path.join(BACKUP_DIR, f'export_all_data_{timestamp}.xlsx')
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            for table in tables['name']:
                df = pd.read_sql(f"SELECT * FROM {table}", conn)
                df.to_excel(writer, sheet_name=table[:31], index=False)  # Excel sheet名最多31字符
        
        conn.close()
        logger.info(f"✅ 数据已导出到: {excel_file}")
        return excel_file
    except Exception as e:
        logger.error(f"❌ 导出数据失败: {e}")
        return False


def export_data_to_csv():
    """导出所有数据到 CSV 文件（每个表一个CSV）"""
    try:
        conn = sqlite3.connect(DB_PATH)
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_dir = os.path.join(BACKUP_DIR, f'csv_export_{timestamp}')
        os.makedirs(csv_dir, exist_ok=True)
        
        for table in tables['name']:
            df = pd.read_sql(f"SELECT * FROM {table}", conn)
            csv_file = os.path.join(csv_dir, f'{table}.csv')
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        conn.close()
        logger.info(f"✅ 数据已导出到: {csv_dir}")
        return csv_dir
    except Exception as e:
        logger.error(f"❌ 导出CSV失败: {e}")
        return False


# ========== 健康检查 ==========
def health_check():
    """检查系统健康状况"""
    status = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'database_ok': False,
        'backup_count': 0,
        'db_size': 0,
        'tables': []
    }
    
    try:
        # 检查数据库
        if os.path.exists(DB_PATH):
            size = os.path.getsize(DB_PATH) / 1024 / 1024  # MB
            status['db_size'] = f"{size:.2f} MB"
            
            conn = sqlite3.connect(DB_PATH)
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
            status['tables'] = tables['name'].tolist()
            conn.close()
            status['database_ok'] = True
        else:
            status['database_ok'] = False
        
        # 备份数量
        status['backup_count'] = len([f for f in os.listdir(BACKUP_DIR) if f.startswith('stock_data_')])
        
        return status
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        status['error'] = str(e)
        return status


# ========== 清理日志 ==========
def clean_old_logs():
    """清理旧的日志文件"""
    try:
        files = [f for f in os.listdir(LOG_DIR) if f.startswith('system_') and f.endswith('.log')]
        files.sort()
        
        if len(files) > MAX_LOGS:
            for f in files[:-MAX_LOGS]:
                os.remove(os.path.join(LOG_DIR, f))
                logger.info(f"   🗑️ 已删除旧日志: {f}")
        
        return len(files)
    except Exception as e:
        logger.error(f"清理日志失败: {e}")
        return 0


# ========== 测试函数 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🧪 测试备份管理模块")
    print("=" * 50)
    
    # 执行备份
    print("\n📦 执行数据库备份...")
    backup_database()
    
    # 列出备份
    print("\n📋 备份列表:")
    for b in list_backups():
        print(f"   {b['name']} ({b['size']}) - {b['time']}")
    
    # 健康检查
    print("\n🏥 系统健康检查:")
    status = health_check()
    print(f"   数据库状态: {'✅ 正常' if status['database_ok'] else '❌ 异常'}")
    print(f"   数据库大小: {status['db_size']}")
    print(f"   备份数量: {status['backup_count']}")
    print(f"   数据表: {', '.join(status['tables'])}")
    
    print("\n✅ 备份管理模块测试完成！")