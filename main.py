"""
第七步：AI炒股工作台 - 系统主入口
整合数据更新、预警监控、网页服务、自动存档
"""

import os
import sys
import time
import threading
import subprocess
import webbrowser
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ========== 配置 ==========
PORT = 5000
UPDATE_INTERVAL = 60  # 数据更新间隔（秒）
ALERT_INTERVAL = 300  # 预警检查间隔（秒）
ARCHIVE_INTERVAL = 30  # 每30次更新存档一次（约30分钟）


def print_banner():
    """打印启动横幅"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      📊 AI 炒股工作台 - 专业版 v8.0                     ║
║                                                          ║
║      🔄 数据监控  |  🔔 预警系统  |  🌐 网页服务        ║
║      📦 自动存档  |  📄 报告生成  |  🧹 自动清理        ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)


def check_database():
    """检查数据库是否存在且有数据"""
    if not os.path.exists('stock_data.db'):
        print("❌ 数据库不存在！")
        print("   请先运行: python step1_get_stock_etf.py")
        return False
    
    try:
        import sqlite3
        conn = sqlite3.connect('stock_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_realtime'")
        result = cursor.fetchone()
        conn.close()
        
        if result is None:
            print("⚠️ 数据库中没有实时数据！")
            print("   请先运行: python step2_realtime_updater.py")
            return False
        
        print("✅ 数据库检查通过")
        return True
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False


def run_web_server():
    """启动网页服务器"""
    print("\n🌐 启动网页服务器...")
    try:
        import app
        app.app.run(debug=False, host='0.0.0.0', port=PORT)
    except Exception as e:
        print(f"❌ 网页服务器启动失败: {e}")
        return False


def run_data_updater():
    """
    运行数据更新（后台线程）
    每60秒更新一次，每30次（约30分钟）自动存档一次
    """
    print("🔄 启动数据更新线程...")
    
    try:
        import step2_realtime_updater as updater
        from data_persistence import archive_realtime_data
        import time
        
        # 首次立即更新
        print("   📡 执行首次数据更新...")
        updater.fetch_all_realtime()
        print("   ✅ 首次数据更新完成")
        
        # 定时循环
        update_count = 0
        while True:
            time.sleep(UPDATE_INTERVAL)
            
            # 执行数据更新
            updater.fetch_all_realtime()
            update_count += 1
            
            # 每30次更新（约30分钟）存档一次
            if update_count % ARCHIVE_INTERVAL == 0:
                print(f"📦 执行自动存档 (第 {update_count} 次更新后)...")
                try:
                    archive_realtime_data()
                except Exception as e:
                    print(f"   ⚠️ 自动存档失败: {e}")
                
                # 同时清理30天前的旧存档
                try:
                    from data_persistence import clean_old_archives
                    deleted = clean_old_archives(days=30)
                    if deleted > 0:
                        print(f"   🧹 已清理 {deleted} 个旧存档文件")
                except Exception as e:
                    print(f"   ⚠️ 清理旧存档失败: {e}")
                    
    except Exception as e:
        print(f"❌ 数据更新线程出错: {e}")


def run_alert_checker():
    """运行预警检查（后台线程）"""
    print("🔔 启动预警检查线程...")
    
    try:
        from alert_system import run_alert_check
        
        # 首次立即检查
        print("   📡 执行首次预警检查...")
        run_alert_check()
        
        # 定时循环
        while True:
            time.sleep(ALERT_INTERVAL)
            run_alert_check()
    except Exception as e:
        print(f"❌ 预警检查线程出错: {e}")


def open_browser():
    """自动打开浏览器"""
    time.sleep(3)
    url = f"http://127.0.0.1:{PORT}"
    print(f"\n🌐 正在打开浏览器: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"⚠️ 无法自动打开浏览器: {e}")
        print(f"   请手动打开: {url}")


def main():
    """主函数"""
    print_banner()
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 检查数据库
    if not check_database():
        print("\n💡 请按以下顺序初始化系统：")
        print("   1. python step1_get_stock_etf.py  # 获取股票列表")
        print("   2. python step2_realtime_updater.py  # 获取实时数据")
        print("\n⚠️ 系统将在 5 秒后退出...")
        time.sleep(5)
        sys.exit(1)
    
    print("\n🚀 正在启动系统组件...")
    print("-" * 60)
    
    # 启动各个线程
    threads = []
    
    # 1. 数据更新线程（含自动存档）
    t1 = threading.Thread(target=run_data_updater, daemon=True)
    t1.start()
    threads.append(t1)
    print("   ✅ 数据更新线程已启动 (每60秒更新，每30分钟存档)")
    
    # 2. 预警检查线程
    t2 = threading.Thread(target=run_alert_checker, daemon=True)
    t2.start()
    threads.append(t2)
    print("   ✅ 预警检查线程已启动 (每5分钟检查)")
    
    # 3. 打开浏览器（延迟执行）
    t3 = threading.Thread(target=open_browser, daemon=True)
    t3.start()
    print("   ✅ 浏览器自动打开（3秒后）")
    
    print("-" * 60)
    print(f"\n🌐 网页服务地址: http://127.0.0.1:{PORT}")
    print("💡 按 Ctrl + C 可以停止所有服务")
    print("=" * 60)
    
    # 4. 启动网页服务器（主线程）
    try:
        run_web_server()
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信号，正在关闭所有服务...")
        print("✅ 系统已停止")
    except Exception as e:
        print(f"❌ 系统运行出错: {e}")
        print("💡 按 Ctrl + C 强制退出")


if __name__ == "__main__":
    main()