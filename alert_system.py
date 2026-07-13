"""
第六步：自动预警系统模块
支持价格预警、涨跌幅预警、桌面弹窗通知
"""

import sqlite3
import pandas as pd
import os
import time
from datetime import datetime
import json

# 尝试导入 plyer（用于桌面通知）
try:
    from plyer import notification
    NOTIFICATION_ENABLED = True
except ImportError:
    NOTIFICATION_ENABLED = False
    print("⚠️ plyer 未安装，桌面通知功能不可用")
    print("   请执行: pip install plyer")

# 数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'stock_data.db')

# 预警配置文件
ALERT_CONFIG_FILE = 'alert_config.json'

# ========== 默认预警配置 ==========
DEFAULT_CONFIG = {
    "alerts": [
        {
            "id": 1,
            "enabled": True,
            "type": "price_above",  # price_above, price_below, change_percent
            "symbol": "000001",
            "name": "平安银行",
            "threshold": 12.00,
            "message": "平安银行股价突破 12.00 元！"
        },
        {
            "id": 2,
            "enabled": True,
            "type": "change_percent",
            "symbol": "000001",
            "name": "平安银行",
            "threshold": 5.0,
            "message": "平安银行涨跌幅超过 5%！"
        },
        {
            "id": 3,
            "enabled": False,
            "type": "price_below",
            "symbol": "600519",
            "name": "贵州茅台",
            "threshold": 1500.00,
            "message": "贵州茅台跌破 1500 元！"
        }
    ]
}


def load_alert_config():
    """
    加载预警配置
    如果配置文件不存在，创建默认配置
    """
    if os.path.exists(ALERT_CONFIG_FILE):
        with open(ALERT_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 创建默认配置文件
        save_alert_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG


def save_alert_config(config):
    """保存预警配置"""
    with open(ALERT_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"✅ 预警配置已保存到 {ALERT_CONFIG_FILE}")


def get_realtime_price(symbol, data_type='stock'):
    """
    从数据库获取股票/基金的最新价格
    """
    try:
        conn = sqlite3.connect(db_path)
        
        if data_type == 'stock':
            df = pd.read_sql(f"SELECT * FROM stock_realtime WHERE 代码='{symbol}'", conn)
        else:
            df = pd.read_sql(f"SELECT * FROM etf_realtime WHERE 代码='{symbol}'", conn)
        
        conn.close()
        
        if df.empty:
            return None
        
        row = df.iloc[0]
        return {
            'symbol': row.get('代码', symbol),
            'name': row.get('名称', ''),
            'price': float(row.get('最新价', 0)),
            'change': float(row.get('涨跌幅', 0)),
            'volume': row.get('成交量', 0),
            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        print(f"❌ 获取价格失败 {symbol}: {e}")
        return None


def send_desktop_notification(title, message, timeout=10):
    """
    发送桌面弹窗通知
    """
    if NOTIFICATION_ENABLED:
        try:
            notification.notify(
                title=title,
                message=message,
                timeout=timeout,
                app_name="AI炒股工作台"
            )
            print(f"🔔 桌面通知已发送: {title}")
            return True
        except Exception as e:
            print(f"❌ 桌面通知发送失败: {e}")
            return False
    else:
        print(f"📢 [通知] {title}: {message}")
        return False


def check_alerts():
    """
    检查所有预警条件
    返回触发的预警列表
    """
    config = load_alert_config()
    triggered = []
    
    for alert in config.get('alerts', []):
        # 检查是否启用
        if not alert.get('enabled', True):
            continue
        
        symbol = alert.get('symbol', '')
        alert_type = alert.get('type', '')
        threshold = alert.get('threshold', 0)
        name = alert.get('name', symbol)
        message = alert.get('message', f'{name} 触发预警')
        
        # 获取实时价格
        data = get_realtime_price(symbol)
        if data is None:
            continue
        
        price = data['price']
        change = data['change']
        
        # 检查预警条件
        should_alert = False
        detail = ""
        
        if alert_type == 'price_above':
            if price >= threshold:
                should_alert = True
                detail = f"当前价格: {price:.2f} >= 阈值: {threshold:.2f}"
        elif alert_type == 'price_below':
            if price <= threshold:
                should_alert = True
                detail = f"当前价格: {price:.2f} <= 阈值: {threshold:.2f}"
        elif alert_type == 'change_percent':
            if abs(change) >= threshold:
                should_alert = True
                detail = f"当前涨跌幅: {change:+.2f}% >= 阈值: {threshold:.2f}%"
        
        if should_alert:
            triggered.append({
                'symbol': symbol,
                'name': name,
                'type': alert_type,
                'price': price,
                'change': change,
                'message': message,
                'detail': detail,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    return triggered


def run_alert_check():
    """
    执行预警检查并发送通知
    """
    print(f"\n🔔 [{datetime.now().strftime('%H:%M:%S')}] 开始预警检查...")
    
    triggered = check_alerts()
    
    if triggered:
        print(f"⚠️ 触发 {len(triggered)} 条预警:")
        for alert in triggered:
            print(f"   - {alert['name']}({alert['symbol']}): {alert['detail']}")
            # 发送桌面通知
            title = f"🚨 预警: {alert['name']}"
            message = f"{alert['message']}\n{alert['detail']}"
            send_desktop_notification(title, message)
    else:
        print("✅ 暂无预警触发")
    
    return triggered


def add_alert(symbol, name, alert_type, threshold, message):
    """
    添加新的预警规则
    """
    config = load_alert_config()
    
    # 生成新的ID
    max_id = max([a.get('id', 0) for a in config.get('alerts', [])]) if config.get('alerts') else 0
    new_id = max_id + 1
    
    new_alert = {
        "id": new_id,
        "enabled": True,
        "type": alert_type,
        "symbol": symbol,
        "name": name,
        "threshold": threshold,
        "message": message
    }
    
    config['alerts'].append(new_alert)
    save_alert_config(config)
    print(f"✅ 已添加预警: {name} {alert_type} {threshold}")
    return new_alert


def delete_alert(alert_id):
    """删除预警规则"""
    config = load_alert_config()
    config['alerts'] = [a for a in config.get('alerts', []) if a.get('id') != alert_id]
    save_alert_config(config)
    print(f"✅ 已删除预警 ID: {alert_id}")


def list_alerts():
    """列出所有预警规则"""
    config = load_alert_config()
    alerts = config.get('alerts', [])
    
    if not alerts:
        print("📭 暂无预警规则")
        return []
    
    print("\n📋 当前预警规则:")
    print("-" * 60)
    for alert in alerts:
        status = "✅ 启用" if alert.get('enabled', True) else "⏸️ 禁用"
        print(f"  [{alert.get('id')}] {status} | {alert.get('name')} | {alert.get('type')} | 阈值: {alert.get('threshold')}")
    print("-" * 60)
    
    return alerts


# ========== 测试函数 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🔔 测试预警系统")
    print("=" * 50)
    
    # 列出当前预警规则
    list_alerts()
    
    # 执行一次预警检查
    print("\n📡 执行预警检查...")
    run_alert_check()
    
    print("\n💡 提示:")
    print("   1. 要添加预警，请编辑 alert_config.json 文件")
    print("   2. 要测试桌面通知，运行: python alert_system.py")