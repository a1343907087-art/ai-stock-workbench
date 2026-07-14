"""
AI 分析模块 - 使用 requests 直接调用 DeepSeek API
彻底解决编码问题
"""

import requests
import json
import os

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# 如果环境变量没有设置，使用默认值（仅用于本地测试）
if not DEEPSEEK_API_KEY:
    DEEPSEEK_API_KEY = "sk-你的DeepSeek API Key"  # 替换成你的真实 Key

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


def chat_with_ai(user_message):
    """
    通用对话功能 - 使用 requests 直接调用
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一位金融投资助手，帮助用户分析股票、基金和投资策略。"},
                {"role": "user", "content": user_message}
            ],
            "stream": False,
            "temperature": 0.8,
            "max_tokens": 800
        }
        
        response = requests.post(DEEPSEEK_URL, headers=headers, json=data, timeout=30)
        
        # 检查响应状态
        if response.status_code != 200:
            return f"API 请求失败: {response.status_code} - {response.text}"
        
        result = response.json()
        
        # 提取回复内容
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return f"API 返回格式异常: {result}"
            
    except Exception as e:
        return f"对话失败: {str(e)}"


def analyze_stock(symbol, name, price, change, volume):
    """
    分析单只股票
    """
    prompt = f"""你是一位专业的股票分析师。请分析以下股票：

股票代码：{symbol}
股票名称：{name}
最新价格：{price}
涨跌幅：{change}%
成交量：{volume}

请从以下角度进行分析：
1. 技术面分析
2. 投资建议
3. 风险提示

请用简洁专业的语言回答，200字以内。"""

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一位专业的股票分析师，擅长技术分析和投资建议。"},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(DEEPSEEK_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            return f"API 请求失败: {response.status_code} - {response.text}"
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return f"API 返回格式异常: {result}"
            
    except Exception as e:
        return f"AI 分析失败: {str(e)}"


def analyze_market(stock_list):
    """
    分析多只股票（市场分析）
    """
    summary = "请分析以下股票组合的市场表现：\n"
    for stock in stock_list:
        summary += f"- {stock['name']}({stock['symbol']}): 价格{stock['price']}, 涨跌幅{stock['change']}%\n"

    prompt = summary + """
请从以下角度分析：
1. 整体市场趋势
2. 板块表现
3. 风险提示
4. 操作建议

请用简洁专业的语言回答，200字以内。"""

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一位资深市场分析师。"},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 600
        }
        
        response = requests.post(DEEPSEEK_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            return f"API 请求失败: {response.status_code} - {response.text}"
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return f"API 返回格式异常: {result}"
            
    except Exception as e:
        return f"市场分析失败: {str(e)}"


# 本地测试
if __name__ == "__main__":
    print("=" * 50)
    print("🧪 测试 AI 分析模块 (requests 版本)")
    print("=" * 50)
    
    # 测试对话
    print("\n💬 测试对话功能...")
    result = chat_with_ai("请分析一下平安银行")
    print(result)
    
    stock_data.db