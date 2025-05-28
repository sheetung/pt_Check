# -*- coding: utf-8 -*-
import os
import requests
import re
import time
import hmac
import hashlib
import base64
import urllib.parse
from bs4 import BeautifulSoup

# 配置
bark_push = os.environ.get("BARK_PUSH", "")
bark_group = "PTlover"
bark_icon = "https://www.ptlover.cc/favicon.ico"
bark_sound = os.environ.get("BARK_SOUND", "")

dingtalk_token = os.environ.get("DD_BOT_TOKEN", "")
dingtalk_secret = os.environ.get("DD_BOT_SECRET", "")

class PTloverClient:
    def __init__(self, cookie):
        self.cookie = cookie

    def sign_in(self):
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Cookie': self.cookie,
        }
        url = 'https://www.ptlover.cc/attendance.php'
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            html = response.text

            # 提取打卡内容（清洗 HTML）
            match = re.search(r'<p>(.*?)</p>', html, re.DOTALL)
            result_text = ""
            if match:
                raw_html = match.group(1)
                result_text = BeautifulSoup(raw_html, 'html.parser').get_text(separator='', strip=True)

            # 提取用户名
            soup = BeautifulSoup(html, 'html.parser')
            username_tag = soup.select_one('span.nowrap a b')
            username = username_tag.text.strip() if username_tag else "未知用户"

            return {
                "status": "success",
                "user": username,
                "message": result_text or "签到成功"
            }
        except Exception as e:
            return {
                "status": "error",
                "user": "未知",
                "message": str(e)
            }

def send_bark_notification(results):
    if not bark_push:
        print("未配置 Bark 推送")
        return

    title = "PTlover 签到通知"
    body_lines = []
    for i, res in enumerate(results, 1):
        line = f"账号{i}（{res['user']}）: {'✅ ' + res['message'] if res['status'] == 'success' else '❌ ' + res['message']}"
        body_lines.append(line)

    params = {
        "title": title,
        "body": "\n".join(body_lines),
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

    title = "PTlover 签到通知"
    text = f"# {title}\n\n"
    for i, res in enumerate(results, 1):
        line = f"账号{i}（{res['user']}）: {'✅ ' + res['message'] if res['status'] == 'success' else '❌ ' + res['message']}"
        text += line + "\n\n"

    data = {
        "msgtype": "markdown",
        "markdown": {"title": title, "text": text}
    }

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
    cookies = os.environ.get("PTLOVER_COOKIES")
    if not cookies:
        print("❌ 未配置 PTLOVER_COOKIES 环境变量")
        return

    cookie_list = cookies.split("&")
    results = []

    for idx, cookie in enumerate(cookie_list, 1):
        print(f"\n➡️ 正在签到账号 {idx}...")
        result = PTloverClient(cookie).sign_in()
        print(f"账号 {idx}（{result['user']}）签到结果：{result['message']}")
        results.append(result)

    # 推送通知
    send_bark_notification(results)
    send_dingtalk_notification(results)

if __name__ == "__main__":
    main()
