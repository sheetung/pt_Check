# -*- coding: utf-8 -*-
import os
import requests
import re
import time
import hmac
import hashlib
import base64
import urllib.parse
import random
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 配置
bark_push = os.environ.get("BARK_PUSH", "")
bark_group = "青蛙签到"
bark_icon = "https://www.qingwapt.com/favicon.ico"
bark_sound = os.environ.get("BARK_SOUND", "")
dingtalk_token = os.environ.get("DD_BOT_TOKEN", "")
dingtalk_secret = os.environ.get("DD_BOT_SECRET", "")

class QingwaClient:
    def __init__(self, cookie):
        self.cookie = cookie
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def sign_in(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36 Edg/137.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cookie': self.cookie,
            'Connection': 'keep-alive',
            'Referer': 'https://www.qingwapt.com/',
        }
        url = 'https://www.qingwapt.com/attendance.php'
        try:
            time.sleep(random.uniform(1, 3))  # 避免请求过快
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            html = response.text

            # 提取签到结果文本
            soup = BeautifulSoup(html, 'html.parser')
            
            # 用户名提取
            username_tag = soup.select_one('.User_Name b')
            username = username_tag.text.strip() if username_tag else "未知用户"
            
            # 签到参数提取
            sign_text = soup.select_one('table[width="100%"] tr td p')
            if not sign_text:
                return {
                    "status": "error",
                    "user": username,
                    "days": "0",
                    "consecutive_days": "0",
                    "current_bonus": 0,
                    "total_bonus": 0.0,
                    "message": "未找到签到结果文本"
                }
                
            sign_text = sign_text.get_text()
            
            # 提取签到天数
            days_match = re.search(r'这是您的第\s*<b>\s*(\d+)\s*</b>\s*次签到', html) or \
                        re.search(r'这是您的第\s*(\d+)\s*次签到', html)
            sign_days = days_match.group(1) if days_match else "未知"
            
            # 连续签到天数
            consecutive_match = re.search(r'已连续签到\s*<b>\s*(\d+)\s*</b>\s*天', html)
            consecutive_days = consecutive_match.group(1) if consecutive_match else "0"
            
            # 本次获得蝌蚪数量
            current_match = re.search(r'本次签到获得\s*<b>\s*(\d+)\s*</b>\s*个蝌蚪', html)
            current_bonus = int(current_match.group(1)) if current_match else 0

            # 总蝌蚪数量（保留原始格式，不转换为浮点数）
            total_bonus = "0.0"  # 默认值改为字符串类型
            bonus_font = soup.find('font', class_='color_bonus', string=lambda text: text and '蝌蚪' in text)
            if bonus_font:
                parent_html = str(bonus_font.parent)
                # 匹配包含逗号和小数点的数值（如 "2,058.0"）
                total_match = re.search(r'蝌蚪.*?:\s*([\d,.]+)', parent_html)
                if total_match:
                    total_bonus = total_match.group(1)  # 直接使用原始匹配结果（保留逗号）
                
            # 每日排名
            rank_match = re.search(r'今日签到排名：\s*<b>\s*(\d+)\s*</b>\s*/\s*<b>\s*(\d+)\s*</b>', html)
            rank = f"{rank_match.group(1)}/{rank_match.group(2)}" if rank_match else "未知"

            return {
                "status": "success",
                "user": username,
                "days": sign_days,
                "consecutive_days": consecutive_days,
                "current_bonus": current_bonus,
                "total_bonus": total_bonus,
                "rank": rank,
                "message": sign_text.replace("点击白色背景的圆点进行补签。", "")
                                     .replace("今日签到排名：", "") 
                                     .replace("<b>", "") 
                                     .replace("</b>", "").strip()
            }
        except Exception as e:
            return {
                "status": "error",
                "user": "未知",
                "days": "0",
                "consecutive_days": "0",
                "current_bonus": 0,
                "total_bonus": 0.0,
                "rank": "未知",
                "message": str(e)
            }

def send_bark_notification(results):
    if not bark_push:
        print("未配置 Bark 推送")
        return

    title = "青蛙签到通知"
    body_lines = []
    for i, res in enumerate(results, 1):
        if res['status'] == 'success':
            line = f"🐸 账号{i}（{res['user']}）\n"
            line += f"✅ 签到{res['days']}天 (连续{res['consecutive_days']}天) 排名[{res['rank']}]\n"
            line += f"本次获得蝌蚪: {res['current_bonus']}个\n"
            line += f"总蝌蚪数量: {res['total_bonus']}个"
        else:
            line = f"🚫 账号{i}（{res['user']}）签到失败\n❌ {res['message']}"
        body_lines.append(line)

    params = {
        "title": title,
        "body": "\n\n".join(body_lines),
        "icon": bark_icon,
        "sound": bark_sound,
        "group": bark_group,
    }

    try:
        resp = requests.post(bark_push, json=params)
        resp.raise_for_status()
        print("✅ Bark 推送成功")
    except Exception as e:
        print(f"❌ Bark 推送失败: {e}")

def send_dingtalk_notification(results):
    if not dingtalk_token:
        print("未配置钉钉推送")
        return

    title = "青蛙签到通知"
    text = f"### {title}\n\n"
    for i, res in enumerate(results, 1):
        if res['status'] == 'success':
            text += f"**🐸 账号{i}（{res['user']}）**\n"
            text += f"- ✅ 签到天数: **{res['days']}** 天 (连续 **{res['consecutive_days']}** 天)\n"
            text += f"- 🏆 排名: **{res['rank']}**\n"
            text += f"- 🪙 本次获得蝌蚪: **{res['current_bonus']}** 个\n"
            text += f"- 🐸 总蝌蚪数量: **{res['total_bonus']}** 个\n\n"
        else:
            text += f"**🚫 账号{i}（{res['user']}）签到失败**\n"
            text += f"- ❌ 错误原因: {res['message']}\n\n"

    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": text
        }
    }

    # 处理加签
    if dingtalk_secret:
        timestamp = str(round(time.time() * 1000))
        secret_enc = dingtalk_secret.encode('utf-8')
        string_to_sign = f"{timestamp}\n{dingtalk_secret}".encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign, hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        url = f"https://oapi.dingtalk.com/robot/send?access_token={dingtalk_token}&timestamp={timestamp}&sign={sign}"
    else:
        url = f"https://oapi.dingtalk.com/robot/send?access_token={dingtalk_token}"

    headers = {"Content-Type": "application/json;charset=utf-8"}
    try:
        resp = requests.post(url, json=data, headers=headers)
        resp.raise_for_status()
        print("✅ 钉钉推送成功")
    except Exception as e:
        print(f"❌ 钉钉推送失败: {e}")

def main():
    # 随机延时 0-600 秒
    delay = random.uniform(0, 600)
    print(f"随机延时 {delay:.2f} 秒后开始签到...")
    time.sleep(delay)
    
    cookies = os.environ.get("QINGWA_COOKIES")
    if not cookies:
        print("❌ 未配置 QINGWA_COOKIES 环境变量")
        return

    cookie_list = cookies.split("&")
    results = []

    for idx, cookie in enumerate(cookie_list, 1):
        print(f"\n➡️ 正在签到账号 {idx}...")
        client = QingwaClient(cookie)
        result = client.sign_in()
        if result['status'] == 'success':
            print(f"✅ 账号 {idx}（{result['user']}）签到成功！")
            print(f"   签到天数: {result['days']}天 (连续 {result['consecutive_days']}天)")
            print(f"   每日排名: {result['rank']}")
            print(f"   本次获得蝌蚪: {result['current_bonus']}个")
            print(f"   总蝌蚪数量: {result['total_bonus']}个")
        else:
            print(f"❌ 账号 {idx}（{result['user']}）签到失败: {result['message']}")
        results.append(result)

    # 推送通知
    send_bark_notification(results)
    send_dingtalk_notification(results)

if __name__ == "__main__":
    main()
