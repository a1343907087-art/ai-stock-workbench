"""
第十步：定时任务调度器
自动备份、日志清理、健康检查
"""

import schedule
import time
from datetime import datetime
from backup_manager import backup_database, clean_old_logs, health_check, logger


def scheduled_backup():
    """定时备份任务"""
    logger.info("⏰ 执行定时备份...")
    backup_database()


def scheduled_cleanup():
    """定时清理任务"""
    logger.info("⏰ 执行定时清理...")
    clean_old_logs()


def scheduled_health_check():
    """定时健康检查任务"""
    status = health_check()
    if not status['database_ok']:
        logger.warning("⚠️ 健康检查: 数据库异常！")
    else:
        logger.info(f"✅ 健康检查: 数据库正常 ({status['db_size']}, {status['backup_count']}个备份)")


def run_scheduler():
    """运行定时调度器"""
    print("=" * 50)
    print("⏰ 定时任务调度器已启动")
    print("=" * 50)
    print("📋 任务列表:")
    print("   - 每天 02:00 备份数据库")
    print("   - 每天 03:00 清理旧日志")
    print("   - 每 6 小时 健康检查")
    print("   - 按 Ctrl+C 停止")
    print("=" * 50)
    
    # 设置定时任务
    schedule.every().day.at("02:00").do(scheduled_backup)
    schedule.every().day.at("03:00").do(scheduled_cleanup)
    schedule.every(6).hours.do(scheduled_health_check)
    
    # 启动时立即执行一次健康检查
    scheduled_health_check()
    
    # 主循环
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # 每30秒检查一次
    except KeyboardInterrupt:
        print("\n🛑 调度器已停止")


if __name__ == "__main__":
    run_scheduler()