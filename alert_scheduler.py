"""
预警调度器 - 定时执行预警检查
"""

import time
import schedule
from alert_system import run_alert_check, list_alerts
from datetime import datetime

def job():
    """定时执行的预警检查任务"""
    print(f"\n{'='*50}")
    print(f"⏰ 定时预警检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    run_alert_check()

def main():
    """主程序"""
    print("=" * 60)
    print("🔔 预警调度器已启动")
    print("=" * 60)
    
    # 显示当前预警规则
    list_alerts()
    
    print("\n⏰ 预警检查计划:")
    print("   - 每 5 分钟检查一次（交易时段）")
    print("   - 按 Ctrl + C 可停止")
    print("=" * 60)
    
    # 立即执行一次
    print("\n📡 立即执行首次检查...")
    job()
    
    # 定时任务：每5分钟执行一次
    schedule.every(5).minutes.do(job)
    
    # 也可以设置在交易时段内执行
    # schedule.every().day.at("09:35").do(job)
    # schedule.every().day.at("10:00").do(job)
    # schedule.every().day.at("10:30").do(job)
    # schedule.every().day.at("11:00").do(job)
    # schedule.every().day.at("13:30").do(job)
    # schedule.every().day.at("14:00").do(job)
    # schedule.every().day.at("14:30").do(job)
    # schedule.every().day.at("15:00").do(job)
    
    print("\n⏰ 调度器运行中...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\n🛑 预警调度器已停止")

if __name__ == "__main__":
    main()