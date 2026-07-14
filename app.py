"""
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from ai_analysis import analyze_stock, chat_with_ai, analyze_market
AI 专业炒股工作台 - 完整版
包含：K线图、技术指标、预警系统、数据存档、报告生成、备份管理
"""
from ai_analysis import analyze_stock, chat_with_ai
from flask import Flask, render_template_string, jsonify, request, send_file
import sqlite3
import pandas as pd
import os
import json
from datetime import datetime
from kline_fetcher import get_stock_kline, get_etf_kline, save_kline_to_db
from indicators import calculate_all_indicators, generate_signals
from alert_system import (
    load_alert_config, save_alert_config, 
    add_alert, delete_alert, list_alerts,
    run_alert_check, send_desktop_notification
)
from data_persistence import archive_realtime_data, get_archive_stats, clean_old_archives
from report_generator import generate_excel_report, generate_portfolio_report
from backup_manager import backup_database, list_backups, restore_backup, export_data_to_excel, health_check

app = Flask(__name__)
db_path = os.path.join(os.path.dirname(__file__), 'stock_data.db')


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/data')
def get_data():
    try:
        conn = sqlite3.connect(db_path)
        try:
            stock_df = pd.read_sql("SELECT * FROM stock_realtime", conn)
        except:
            stock_df = pd.DataFrame()
        try:
            etf_df = pd.read_sql("SELECT * FROM etf_realtime", conn)
        except:
            etf_df = pd.DataFrame()
        conn.close()
        
        stock_data = stock_df.to_dict('records') if not stock_df.empty else []
        etf_data = etf_df.to_dict('records') if not etf_df.empty else []
        
        return jsonify({
            'success': True,
            'stock': stock_data,
            'etf': etf_data,
            'stock_count': len(stock_data),
            'etf_count': len(etf_data),
            'total': len(stock_data) + len(etf_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/search')
def search():
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return get_data()
    
    try:
        conn = sqlite3.connect(db_path)
        stock_df = pd.read_sql("SELECT * FROM stock_realtime", conn)
        etf_df = pd.read_sql("SELECT * FROM etf_realtime", conn)
        conn.close()
        
        if not stock_df.empty:
            stock_df = stock_df[
                stock_df['代码'].str.contains(keyword, case=False) |
                stock_df['名称'].str.contains(keyword, case=False)
            ]
        if not etf_df.empty:
            etf_df = etf_df[
                etf_df['代码'].str.contains(keyword, case=False) |
                etf_df['名称'].str.contains(keyword, case=False)
            ]
        
        stock_data = stock_df.to_dict('records') if not stock_df.empty else []
        etf_data = etf_df.to_dict('records') if not etf_df.empty else []
        
        return jsonify({
            'success': True,
            'stock': stock_data,
            'etf': etf_data,
            'stock_count': len(stock_data),
            'etf_count': len(etf_data),
            'total': len(stock_data) + len(etf_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/kline')
def get_kline():
    symbol = request.args.get('symbol', '000001')
    data_type = request.args.get('type', 'stock')
    days = request.args.get('days', 120, type=int)
    
    try:
        conn = sqlite3.connect(db_path)
        table_name = f'kline_{data_type}_{symbol}'
        try:
            df = pd.read_sql(f"SELECT * FROM {table_name} ORDER BY trade_date DESC LIMIT {days}", conn)
        except:
            df = pd.DataFrame()
        conn.close()
        
        if df.empty:
            if data_type == 'etf':
                df = get_etf_kline(symbol, days=days)
            else:
                df = get_stock_kline(symbol, days=days)
            if not df.empty:
                save_kline_to_db(symbol, df, data_type)
        
        if df.empty:
            return jsonify({'success': False, 'error': '暂无数据'})
        
        df = df.sort_values('trade_date')
        df = calculate_all_indicators(df)
        df = generate_signals(df)
        
        data = df.to_dict('records')
        last_signal = df.iloc[-1].get('signal', 'hold') if not df.empty else 'hold'
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'data': data,
            'count': len(data),
            'last_signal': last_signal
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/analyze')
def analyze_stock():
    symbol = request.args.get('symbol', '000001')
    name = request.args.get('name', '')
    days = request.args.get('days', 60, type=int)
    
    try:
        conn = sqlite3.connect(db_path)
        table_name = f'kline_stock_{symbol}'
        try:
            df = pd.read_sql(f"SELECT * FROM {table_name} ORDER BY trade_date DESC LIMIT {days}", conn)
        except:
            df = pd.DataFrame()
        conn.close()
        
        if df.empty:
            return jsonify({'success': False, 'error': '暂无数据，请先加载K线图'})
        
        df = df.sort_values('trade_date')
        df = calculate_all_indicators(df)
        df = generate_signals(df)
        
        latest = df.iloc[-1]
        
        report = f"""


📊 {name or symbol} AI 技术分析报告
================================
📈 最新价格: {latest.get('close', 0):.2f}
📊 成交量: {latest.get('volume', 0):,.0f}

📉 均线系统:
   MA5: {latest.get('ma_5', 0):.2f}
   MA10: {latest.get('ma_10', 0):.2f}
   MA20: {latest.get('ma_20', 0):.2f}
   MA60: {latest.get('ma_60', 0):.2f}

📊 技术指标:
   RSI: {latest.get('rsi', 0):.1f}
   MACD: {latest.get('macd', 0):.3f}
   MACD信号: {latest.get('macd_signal', 0):.3f}
   KDJ_K: {latest.get('kdj_k', 0):.1f}
   KDJ_D: {latest.get('kdj_d', 0):.1f}
   KDJ_J: {latest.get('kdj_j', 0):.1f}

📈 布林带:
   上轨: {latest.get('bb_upper', 0):.2f}
   中轨: {latest.get('bb_middle', 0):.2f}
   下轨: {latest.get('bb_lower', 0):.2f}

🎯 交易信号: {latest.get('signal', 'hold').upper()}

💡 综合建议:
"""
        rsi = latest.get('rsi', 50)
        signal = latest.get('signal', 'hold')
        
        if signal == 'buy':
            report += "   ✅ 出现买入信号，建议关注入场机会。"
        elif signal == 'sell':
            report += "   ⚠️ 出现卖出信号，建议考虑止盈或止损。"
        elif rsi < 30:
            report += "   📉 RSI 处于超卖区域，可能存在反弹机会。"
        elif rsi > 70:
            report += "   📈 RSI 处于超买区域，短期可能有回调风险。"
        else:
            report += "   ⏳ 无明确信号，建议继续持有或观望。"
        
        return jsonify({'success': True, 'report': report})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/alerts')
def get_alerts():
    try:
        config = load_alert_config()
        alerts = config.get('alerts', [])
        return jsonify({'success': True, 'alerts': alerts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/alerts/add', methods=['POST'])
def add_alert_api():
    try:
        data = request.get_json()
        symbol = data.get('symbol', '')
        name = data.get('name', symbol)
        alert_type = data.get('type', 'price_above')
        threshold = float(data.get('threshold', 0))
        message = data.get('message', f'{name} 触发预警')
        
        result = add_alert(symbol, name, alert_type, threshold, message)
        return jsonify({'success': True, 'alert': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/alerts/delete/<int:alert_id>', methods=['DELETE'])
def delete_alert_api(alert_id):
    try:
        delete_alert(alert_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/alerts/check')
def check_alerts_api():
    try:
        triggered = run_alert_check()
        return jsonify({
            'success': True,
            'triggered': triggered,
            'count': len(triggered)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/alerts/test_notification')
def test_notification():
    try:
        send_desktop_notification(
            "🔔 测试通知",
            "AI炒股工作台 预警系统测试成功！"
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/archive')
def archive_data():
    try:
        result = archive_realtime_data()
        return jsonify({'success': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/archive_stats')
def get_archive_stats_api():
    try:
        stats = get_archive_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/generate_report')
def generate_report():
    symbol = request.args.get('symbol', '000001')
    name = request.args.get('name', '')
    
    try:
        result = generate_excel_report(symbol, name)
        if result:
            return jsonify({'success': True, 'file': result})
        else:
            return jsonify({'success': False, 'error': '生成报告失败'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/clean_archive')
def clean_archive():
    days = request.args.get('days', 30, type=int)
    try:
        result = clean_old_archives(days)
        return jsonify({'success': True, 'deleted': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============================================================
# ========== 第十步：备份管理 API ==========
# ============================================================

@app.route('/api/backup')
def api_backup():
    """手动触发备份"""
    try:
        result = backup_database()
        return jsonify({'success': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/backups')
def api_list_backups():
    """列出所有备份"""
    try:
        backups = list_backups()
        return jsonify({'success': True, 'backups': backups})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/restore/<backup_name>')
def api_restore_backup(backup_name):
    """恢复备份"""
    try:
        result = restore_backup(backup_name)
        return jsonify({'success': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/export_excel')
def api_export_excel():
    """导出数据到Excel"""
    try:
        result = export_data_to_excel()
        if result:
            return jsonify({'success': True, 'file': result})
        else:
            return jsonify({'success': False, 'error': '导出失败'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/health')
def api_health():
    """健康检查"""
    try:
        status = health_check()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============================================================
# HTML 模板
# ============================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>📊 AI 专业炒股工作台</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: #f0f2f5;
            padding: 15px;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: white;
            padding: 15px 25px;
            border-radius: 12px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        .header h1 { font-size: 20px; }
        .header h1 span { font-size: 12px; font-weight: 400; color: #888; margin-left: 10px; }
        .header .stats { display: flex; gap: 10px; font-size: 12px; flex-wrap: wrap; }
        .header .stats span { background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 20px; }
        
        .main-layout { display: flex; gap: 15px; }
        .left-panel { flex: 1; min-width: 0; }
        .right-panel { width: 430px; flex-shrink: 0; display: flex; flex-direction: column; gap: 15px; }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .card-title {
            font-size: 14px;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        .card-title .sub { font-weight: 400; font-size: 12px; color: #999; }
        
        .controls {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
            flex-wrap: wrap;
            align-items: center;
        }
        .controls input {
            flex: 1;
            min-width: 100px;
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 13px;
        }
        .controls input:focus { outline: none; border-color: #1a1a2e; }
        .controls button {
            padding: 8px 14px;
            background: #1a1a2e;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 12px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .controls button:hover { background: #2d2d4a; }
        .controls button.green { background: #27ae60; }
        .controls button.green:hover { background: #2ecc71; }
        .controls button.red { background: #e74c3c; }
        .controls button.red:hover { background: #c0392b; }
        .controls button.orange { background: #f39c12; }
        .controls button.orange:hover { background: #e67e22; }
        .controls button.outline { background: transparent; color: #1a1a2e; border: 2px solid #ddd; }
        .controls button.outline:hover { background: #f0f0f0; }
        .controls button.purple { background: #8e44ad; }
        .controls button.purple:hover { background: #9b59b6; }
        
        .table-scroll { overflow-x: auto; max-height: 280px; overflow-y: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        thead { position: sticky; top: 0; z-index: 10; }
        th {
            background: #1a1a2e;
            color: white;
            padding: 6px 8px;
            text-align: left;
            white-space: nowrap;
            font-size: 10px;
        }
        td { padding: 5px 8px; border-bottom: 1px solid #eee; white-space: nowrap; font-size: 11px; }
        tr:hover { background: #f8f9fa; }
        tr.clickable { cursor: pointer; }
        tr.clickable:hover { background: #e8f0fe; }
        
        .up { color: #e74c3c; font-weight: 600; }
        .down { color: #2ecc71; font-weight: 600; }
        
        .tag {
            display: inline-block;
            padding: 1px 8px;
            border-radius: 10px;
            font-size: 9px;
            font-weight: 600;
        }
        .tag-stock { background: #e8f0fe; color: #1a73e8; }
        .tag-etf { background: #fce8e6; color: #d93025; }
        .tag-buy { background: #e8f5e9; color: #27ae60; }
        .tag-sell { background: #fce8e6; color: #e74c3c; }
        .tag-hold { background: #f5f5f5; color: #999; }
        
        #klineChart { width: 100%; height: 260px; }
        
        .analysis-box {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 10px;
            font-size: 11px;
            line-height: 1.8;
            white-space: pre-wrap;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
        }
        
        .signal-badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 16px;
            font-size: 11px;
            font-weight: 700;
        }
        .signal-buy { background: #e8f5e9; color: #27ae60; }
        .signal-sell { background: #fce8e6; color: #e74c3c; }
        .signal-hold { background: #f5f5f5; color: #999; }
        
        .alert-list { max-height: 100px; overflow-y: auto; }
        .alert-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 4px 8px;
            border-bottom: 1px solid #f0f0f0;
            font-size: 11px;
        }
        .alert-item .delete-btn { color: #e74c3c; cursor: pointer; font-weight: 700; padding: 0 4px; }
        .alert-item .delete-btn:hover { color: #c0392b; }
        .alert-form { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
        .alert-form input, .alert-form select {
            padding: 5px 8px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 11px;
        }
        .alert-form button {
            padding: 5px 12px;
            background: #27ae60;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 11px;
            cursor: pointer;
        }
        .alert-form button:hover { background: #2ecc71; }
        
        .loading-text { text-align: center; padding: 20px; color: #999; font-size: 13px; }
        
        .tools-row {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 8px;
        }
        .tools-row button {
            padding: 6px 14px;
            border: none;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .tools-row .btn-archive { background: #3498db; color: white; }
        .tools-row .btn-archive:hover { background: #2980b9; }
        .tools-row .btn-report { background: #2ecc71; color: white; }
        .tools-row .btn-report:hover { background: #27ae60; }
        .tools-row .btn-clean { background: #e67e22; color: white; }
        .tools-row .btn-clean:hover { background: #d35400; }
        
        /* 🆕 备份管理按钮 */
        .tools-row .btn-backup { background: #8e44ad; color: white; }
        .tools-row .btn-backup:hover { background: #9b59b6; }
        .tools-row .btn-export { background: #1abc9c; color: white; }
        .tools-row .btn-export:hover { background: #16a085; }
        
        .backup-list {
            max-height: 120px;
            overflow-y: auto;
            font-size: 12px;
        }
        .backup-item {
            display: flex;
            justify-content: space-between;
            padding: 4px 8px;
            border-bottom: 1px solid #f0f0f0;
        }
        .backup-item .restore-btn {
            color: #27ae60;
            cursor: pointer;
            font-weight: 600;
        }
        .backup-item .restore-btn:hover { color: #2ecc71; }
        
        @media (max-width: 900px) {
            .main-layout { flex-direction: column; }
            .right-panel { width: 100%; }
        }
    </style>
</head>
<body>

<div class="header">
    <h1>📊 AI 专业炒股工作台 <span>v10.0 - 完整版</span></h1>
    <div class="stats">
        <span id="totalCount">📈 加载中...</span>
        <span id="stockCount">📊 股票: --</span>
        <span id="etfCount">📊 ETF: --</span>
        <span id="updateTime">🔄 --</span>
        <span id="alertCount" style="background:#e74c3c;">🔔 预警: --</span>
    </div>
</div>

<div class="main-layout">
    <div class="left-panel">
        <div class="controls">
            <input type="text" id="searchInput" placeholder="🔍 搜索代码或名称..." onkeyup="handleSearch(event)">
            <button onclick="loadData()">🔄 刷新</button>
            <button class="outline" onclick="clearSearch()">✕ 清除</button>
            <button class="orange" onclick="checkAlerts()">🔔 检查预警</button>
        </div>
        
        <!-- 🆕 备份管理 -->
        <div class="card">
            <div class="card-title">💾 备份管理 <span class="sub">数据安全 | 一键恢复</span></div>
            <div class="tools-row">
                <button class="btn-backup" onclick="doBackup()">📦 立即备份</button>
                <button class="btn-export" onclick="doExport()">📊 导出Excel</button>
                <button class="btn-clean" onclick="refreshBackupList()">🔄 刷新列表</button>
            </div>
            <div id="backupStatus" style="margin-top:6px;font-size:12px;color:#666;">💡 点击"立即备份"保存当前数据</div>
            <div class="backup-list" id="backupList">
                <div class="loading-text">⏳ 加载备份列表...</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">🛠️ 工具 <span class="sub">存档 | 报告</span></div>
            <div class="tools-row">
                <button class="btn-archive" onclick="archiveData()">📦 立即存档</button>
                <button class="btn-report" onclick="generateReport()">📄 生成报告</button>
                <button class="btn-clean" onclick="cleanArchive()">🧹 清理存档</button>
            </div>
            <div id="toolStatus" style="margin-top:8px;font-size:12px;color:#666;">💡 点击按钮执行操作</div>
        </div>
        
        <div class="card">
            <div class="card-title">
                🔔 预警管理
                <span class="sub" id="alertStatus">点击"检查预警"手动触发</span>
            </div>
            <div class="alert-list" id="alertList">
                <div class="loading-text">⏳ 加载预警配置...</div>
            </div>
            <div class="alert-form">
                <input type="text" id="alertSymbol" placeholder="代码" style="width:70px;">
                <input type="text" id="alertName" placeholder="名称" style="width:60px;">
                <select id="alertType" style="width:100px;">
                    <option value="price_above">价格突破</option>
                    <option value="price_below">价格跌破</option>
                    <option value="change_percent">涨跌幅</option>
                </select>
                <input type="number" id="alertThreshold" placeholder="阈值" style="width:60px;">
                <button onclick="addAlert()">添加预警</button>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">📋 实时行情 <span class="sub">点击股票查看K线</span></div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>类型</th>
                            <th>代码</th>
                            <th>名称</th>
                            <th>最新价</th>
                            <th>涨跌幅</th>
                            <th>成交量</th>
                            <th>成交额</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                        <tr><td colspan="7" class="loading-text">⏳ 正在加载数据...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <div class="right-panel">
        <div class="card">
            <div class="card-title">
                📈 K线图
                <span class="sub" id="klineSymbol">请点击表格中的股票</span>
                <span id="signalBadge"></span>
            </div>
            <div id="klineChart"></div>
        </div>
        
        <div class="card">
            <div class="card-title">
                🤖 AI 智能分析
                <button class="green" style="padding:3px 10px;font-size:11px;" onclick="analyzeStock()">生成分析</button>
            </div>
            <div class="analysis-box" id="analysisBox">💡 点击"生成分析"获取AI分析报告</div>
        </div>
    </div>
</div>

<script>
    let currentData = { stock: [], etf: [] };
    let selectedSymbol = '000001';
    let selectedName = '平安银行';
    let selectedType = 'stock';
    let klineChart = null;

    function initChart() {
        const dom = document.getElementById('klineChart');
        klineChart = echarts.init(dom);
        window.addEventListener('resize', () => klineChart.resize());
    }

    function loadData() {
        fetch('/api/data')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    currentData.stock = data.stock;
                    currentData.etf = data.etf;
                    updateStats(data);
                    renderTable();
                } else {
                    document.getElementById('tableBody').innerHTML =
                        '<tr><td colspan="7" class="loading-text">❌ ' + data.error + '</td></tr>';
                }
            })
            .catch(() => {
                document.getElementById('tableBody').innerHTML =
                    '<tr><td colspan="7" class="loading-text">❌ 网络错误</td></tr>';
            });
        loadAlerts();
        loadBackups();
    }

    function updateStats(data) {
        document.getElementById('totalCount').textContent = '📈 共 ' + data.total + ' 个标的';
        document.getElementById('stockCount').textContent = '📊 股票: ' + data.stock_count;
        document.getElementById('etfCount').textContent = '📊 ETF: ' + data.etf_count;
        document.getElementById('updateTime').textContent = '🔄 ' + new Date().toLocaleTimeString();
    }

    function renderTable() {
        let data = [];
        data = data.concat(currentData.stock.map(item => ({ ...item, _type: '股票' })));
        data = data.concat(currentData.etf.map(item => ({ ...item, _type: 'ETF' })));

        if (data.length === 0) {
            document.getElementById('tableBody').innerHTML =
                '<tr><td colspan="7" class="loading-text">📭 暂无数据</td></tr>';
            return;
        }

        let html = '';
        data.forEach(item => {
            const change = parseFloat(item['涨跌幅']) || 0;
            const changeClass = change >= 0 ? 'up' : 'down';
            const tagClass = item._type === '股票' ? 'tag-stock' : 'tag-etf';
            const code = item['代码'] || '';
            const name = item['名称'] || '';

            html += '<tr class="clickable" onclick="selectStock(\'' + code + '\', \'' + name + '\', \'stock\')">';
            html += '<td><span class="tag ' + tagClass + '">' + item._type + '</span></td>';
            html += '<td>' + code + '</td>';
            html += '<td>' + name + '</td>';
            html += '<td>' + (item['最新价'] || '') + '</td>';
            html += '<td class="' + changeClass + '">' + (change >= 0 ? '+' : '') + change.toFixed(2) + '%</td>';
            html += '<td>' + formatNumber(item['成交量']) + '</td>';
            html += '<td>' + formatNumber(item['成交额']) + '</td>';
            html += '</tr>';
        });

        document.getElementById('tableBody').innerHTML = html;
    }

    function formatNumber(val) {
        if (!val) return '';
        const num = parseFloat(val);
        if (isNaN(num)) return val;
        if (num >= 100000000) return (num / 100000000).toFixed(2) + '亿';
        if (num >= 10000) return (num / 10000).toFixed(2) + '万';
        return num.toString();
    }

    function selectStock(symbol, name, type) {
        if (!symbol) return;
        selectedSymbol = symbol;
        selectedName = name || symbol;
        selectedType = type || 'stock';
        document.getElementById('klineSymbol').textContent = '📊 ' + name + ' (' + symbol + ')';
        loadKline(symbol, type);
    }

    function loadKline(symbol, type) {
        if (!klineChart) initChart();
        klineChart.showLoading();
        
        fetch('/api/kline?symbol=' + symbol + '&type=' + (type || 'stock') + '&days=120')
            .then(res => res.json())
            .then(data => {
                klineChart.hideLoading();
                if (data.success && data.data && data.data.length > 0) {
                    renderKline(data.data);
                    const badge = document.getElementById('signalBadge');
                    if (data.last_signal === 'buy') {
                        badge.innerHTML = '<span class="signal-badge signal-buy">📈 买入</span>';
                    } else if (data.last_signal === 'sell') {
                        badge.innerHTML = '<span class="signal-badge signal-sell">📉 卖出</span>';
                    } else {
                        badge.innerHTML = '<span class="signal-badge signal-hold">⏸️ 持有</span>';
                    }
                }
            })
            .catch(() => { klineChart.hideLoading(); });
    }

    function renderKline(data) {
        const dates = data.map(d => d.trade_date);
        const kData = data.map(d => [d.open, d.close, d.low, d.high]);
        const ma5 = data.map(d => d.ma_5 || null);
        const ma20 = data.map(d => d.ma_20 || null);

        const option = {
            tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
            legend: { data: ['K线', 'MA5', 'MA20'], top: 3, left: 'center', textStyle: { fontSize: 9 } },
            grid: { left: '5%', right: '5%', top: '18%', bottom: '10%' },
            xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 8 } },
            yAxis: { type: 'value', scale: true },
            series: [
                {
                    name: 'K线',
                    type: 'candlestick',
                    data: kData,
                    itemStyle: { color: '#e74c3c', color0: '#2ecc71', borderColor: '#e74c3c', borderColor0: '#2ecc71' }
                },
                {
                    name: 'MA5',
                    type: 'line',
                    data: ma5,
                    smooth: true,
                    lineStyle: { color: '#f39c12', width: 1 },
                    symbol: 'none'
                },
                {
                    name: 'MA20',
                    type: 'line',
                    data: ma20,
                    smooth: true,
                    lineStyle: { color: '#3498db', width: 1 },
                    symbol: 'none'
                }
            ]
        };

        klineChart.setOption(option);
        klineChart.resize();
    }

    function analyzeStock() {
        if (!selectedSymbol) {
            document.getElementById('analysisBox').textContent = '⚠️ 请先点击选择一只股票';
            return;
        }
        const box = document.getElementById('analysisBox');
        box.textContent = '⏳ 正在分析 ' + selectedName + '...';
        
        fetch('/api/analyze?symbol=' + selectedSymbol + '&name=' + encodeURIComponent(selectedName))
            .then(res => res.json())
            .then(data => {
                box.textContent = data.success ? data.report : '❌ ' + data.error;
            })
            .catch(err => { box.textContent = '❌ 网络错误'; });
    }

    // ========== 预警管理 ==========
    function loadAlerts() {
        fetch('/api/alerts')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    renderAlerts(data.alerts);
                }
            });
    }

    function renderAlerts(alerts) {
        const container = document.getElementById('alertList');
        const countEl = document.getElementById('alertCount');
        
        if (!alerts || alerts.length === 0) {
            container.innerHTML = '<div class="loading-text">📭 暂无预警规则</div>';
            countEl.textContent = '🔔 预警: 0';
            return;
        }
        
        const enabled = alerts.filter(a => a.enabled).length;
        countEl.textContent = '🔔 预警: ' + enabled;
        
        let html = '';
        alerts.forEach(alert => {
            const status = alert.enabled ? '✅' : '⏸️';
            const typeMap = {
                'price_above': '价格突破',
                'price_below': '价格跌破',
                'change_percent': '涨跌幅'
            };
            html += `
                <div class="alert-item">
                    <span>${status} ${alert.name} ${typeMap[alert.type]||alert.type} ${alert.threshold}</span>
                    <span><span class="delete-btn" onclick="deleteAlert(${alert.id})">✕</span></span>
                </div>
            `;
        });
        container.innerHTML = html;
    }

    function addAlert() {
        const symbol = document.getElementById('alertSymbol').value.trim();
        const name = document.getElementById('alertName').value.trim();
        const type = document.getElementById('alertType').value;
        const threshold = parseFloat(document.getElementById('alertThreshold').value);
        
        if (!symbol || !name || !threshold) {
            alert('请完整填写代码、名称和阈值');
            return;
        }
        
        fetch('/api/alerts/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, name, type, threshold })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                document.getElementById('alertSymbol').value = '';
                document.getElementById('alertName').value = '';
                document.getElementById('alertThreshold').value = '';
                loadAlerts();
            } else {
                alert('添加失败: ' + data.error);
            }
        });
    }

    function deleteAlert(id) {
        if (!confirm('确定删除此预警规则吗？')) return;
        fetch('/api/alerts/delete/' + id, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) loadAlerts();
            });
    }

    function checkAlerts() {
        document.getElementById('alertStatus').textContent = '⏳ 检查中...';
        fetch('/api/alerts/check')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const msg = data.count > 0 ? `⚠️ 触发 ${data.count} 条预警` : '✅ 暂无预警触发';
                    document.getElementById('alertStatus').textContent = msg;
                    if (data.count > 0) {
                        alert('⚠️ 触发 ' + data.count + ' 条预警！\n请查看桌面通知。');
                    }
                } else {
                    document.getElementById('alertStatus').textContent = '❌ ' + data.error;
                }
            });
    }

    // ========== 工具功能 ==========
    function archiveData() {
        const status = document.getElementById('toolStatus');
        status.textContent = '⏳ 正在存档数据...';
        fetch('/api/archive')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    status.textContent = '✅ 数据存档成功！';
                } else {
                    status.textContent = '❌ 存档失败: ' + data.error;
                }
            })
            .catch(() => { status.textContent = '❌ 网络错误'; });
    }

    function generateReport() {
        if (!selectedSymbol) {
            alert('请先在表格中点击选择一只股票');
            return;
        }
        const status = document.getElementById('toolStatus');
        status.textContent = '⏳ 正在生成报告...';
        fetch('/api/generate_report?symbol=' + selectedSymbol + '&name=' + encodeURIComponent(selectedName))
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    status.textContent = '✅ 报告已生成: ' + data.file;
                } else {
                    status.textContent = '❌ 生成失败: ' + data.error;
                }
            })
            .catch(() => { status.textContent = '❌ 网络错误'; });
    }

    function cleanArchive() {
        if (!confirm('确定要清理30天前的存档数据吗？')) return;
        const status = document.getElementById('toolStatus');
        status.textContent = '⏳ 正在清理...';
        fetch('/api/clean_archive?days=30')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    status.textContent = '✅ 已清理 ' + data.deleted + ' 个旧文件';
                } else {
                    status.textContent = '❌ 清理失败: ' + data.error;
                }
            })
            .catch(() => { status.textContent = '❌ 网络错误'; });
    }

    // ========== 🆕 备份管理功能 ==========
    function loadBackups() {
        fetch('/api/backups')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    renderBackups(data.backups);
                }
            });
    }

    function renderBackups(backups) {
        const container = document.getElementById('backupList');
        if (!backups || backups.length === 0) {
            container.innerHTML = '<div class="loading-text">📭 暂无备份</div>';
            return;
        }
        let html = '';
        backups.forEach(b => {
            html += `
                <div class="backup-item">
                    <span>📦 ${b.name}</span>
                    <span>${b.size} | ${b.time}</span>
                    <span class="restore-btn" onclick="restoreBackup('${b.name}')">↩️ 恢复</span>
                </div>
            `;
        });
        container.innerHTML = html;
    }

    function refreshBackupList() {
        document.getElementById('backupList').innerHTML = '<div class="loading-text">⏳ 刷新中...</div>';
        loadBackups();
    }

    function doBackup() {
        const status = document.getElementById('backupStatus');
        status.textContent = '⏳ 正在备份...';
        fetch('/api/backup')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    status.textContent = '✅ 备份成功！';
                    loadBackups();
                } else {
                    status.textContent = '❌ 备份失败: ' + data.error;
                }
            })
            .catch(() => { status.textContent = '❌ 网络错误'; });
    }

    function restoreBackup(backupName) {
        if (!confirm('确定要从 ' + backupName + ' 恢复数据吗？当前数据将被覆盖！')) return;
        const status = document.getElementById('backupStatus');
        status.textContent = '⏳ 正在恢复...';
        fetch('/api/restore/' + encodeURIComponent(backupName))
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    status.textContent = '✅ 恢复成功！请刷新页面查看。';
                    alert('✅ 数据恢复成功！请刷新页面。');
                } else {
                    status.textContent = '❌ 恢复失败: ' + data.error;
                }
            })
            .catch(() => { status.textContent = '❌ 网络错误'; });
    }

    function doExport() {
        const status = document.getElementById('backupStatus');
        status.textContent = '⏳ 正在导出数据...';
        fetch('/api/export_excel')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    status.textContent = '✅ 数据已导出: ' + data.file;
                } else {
                    status.textContent = '❌ 导出失败: ' + data.error;
                }
            })
            .catch(() => { status.textContent = '❌ 网络错误'; });
    }

    // ========== 搜索 ==========
    function handleSearch(e) {
        if (e.key === 'Enter') {
            const keyword = document.getElementById('searchInput').value.trim();
            if (keyword) {
                fetch('/api/search?keyword=' + encodeURIComponent(keyword))
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            currentData.stock = data.stock;
                            currentData.etf = data.etf;
                            updateStats(data);
                            renderTable();
                        }
                    });
            } else {
                loadData();
            }
        }
    }

    function clearSearch() {
        document.getElementById('searchInput').value = '';
        loadData();
    }

    // ========== 初始化 ==========
    initChart();
    loadData();
    setTimeout(() => { selectStock('000001', '平安银行', 'stock'); }, 1500);
    setInterval(loadData, 60000);
</script>
</body>
</html>
'''
# ========== AI 分析 API ==========

@app.route('/api/ai/analyze', methods=['POST'])
def ai_analyze_stock():
    """AI 分析单只股票 - 强制 UTF-8"""
    try:
        raw_data = request.get_data(as_text=True)
        if not raw_data:
            return jsonify({'success': False, 'error': '请提供股票信息'})
        
        import json
        try:
            data = json.loads(raw_data)
        except:
            return jsonify({'success': False, 'error': 'JSON 格式错误'})
        
        symbol = data.get('symbol', '')
        name = data.get('name', symbol)
        price = data.get('price', 0)
        change = data.get('change', 0)
        volume = data.get('volume', 0)
        
        if not symbol:
            return jsonify({'success': False, 'error': '请提供股票代码'})
        
        result = analyze_stock(symbol, name, price, change, volume)
        
        if isinstance(result, str):
            result = result.encode('utf-8', errors='ignore').decode('utf-8')
        
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """AI 对话 - 强制 UTF-8"""
    try:
        # 获取原始数据
        raw_data = request.get_data(as_text=True)
        if not raw_data:
            return jsonify({'success': False, 'error': '请提供消息'})
        
        # 手动解析 JSON
        import json
        try:
            data = json.loads(raw_data)
        except:
            return jsonify({'success': False, 'error': 'JSON 格式错误'})
        
        message = data.get('message', '')
        if not message:
            return jsonify({'success': False, 'error': '请输入问题'})
        
        # 调用 AI
        result = chat_with_ai(message)
        
        # 强制 UTF-8 编码
        if isinstance(result, str):
            result = result.encode('utf-8', errors='ignore').decode('utf-8')
        
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("=" * 60)
    print("🌐 启动AI炒股工作台 v10.0 - 完整版")
    print("=" * 60)
    print("📊 访问: http://127.0.0.1:5000")
    print("💡 新增功能：")
    print("   - 💾 一键备份数据库")
    print("   - 📊 导出数据到Excel")
    print("   - ↩️ 一键恢复备份")
    print("💡 按 Ctrl + C 停止")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)