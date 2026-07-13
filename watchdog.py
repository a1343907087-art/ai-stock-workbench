"""
第十步：进程守护脚本
当 main.py 崩溃时自动重启
"""

import subprocess
import time
import os
from datetime import datetime


def run_with_watchdog():
    """运行 main.py 并在崩溃时重启"""
    print("=" * 50)
    print("🛡️ 进程守护已启动")
    print("=" * 50)
    print("📋 监控目标: main.py")
    print("💡 按 Ctrl+C 停止所有进程")
    print("=" * 50)
    
    while True:
        try:
            print(f"\n🚀 [{datetime.now().strftime('%H:%M:%S')}] 启动 main.py...")
            
            # 启动 main.py
            process = subprocess.Popen(
                ['python', 'main.py'],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # 等待进程结束
            process.wait()
            
            print(f"⚠️ [{datetime.now().strftime('%H:%M:%S')}] main.py 已停止，5秒后重启...")
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号，正在关闭...")
            if 'process' in locals():
                process.terminate()
            break
        except Exception as e:
            print(f"❌ 守护进程出错: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_with_watchdog()