def send_dingtalk_notification(results):
    if not dingtalk_token:
        print("未配置钉钉推送")
        return

    title = "青蛙签到通知"
    text = f"# {title}\n\n"
    for i, res in enumerate(results, 1):
        if res['status'] == 'success':
            text += f"### 🐸 账号{i}（{res['user']}）\n"
            text += f"- ✅ 签到天数: **{res['days']}** 天 (连续 **{res['consecutive_days']}** 天)\n"
            text += f"- 🏆 排名: **{res['rank']}**\n"
            text += f"- 🪙 本次获得蝌蚪: **{res['current_bonus']}** 个\n"
            text += f"- 🐸 总蝌蚪数量: **{res['total_bonus']:,.1f}** 个\n\n"
        else:
            text += f"### 🚫 账号{i}（{res['user']}）签到失败\n"
            text += f"- ❌ 错误原因: {res['message']}\n\n"

    data = {
        "msgtype": "markdown",
        "markdown": {"title": title, "text": text}
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
        print("钉钉数据准备发送:", data)  # 调试输出
        resp = requests.post(url, json=data, headers=headers)
        print("钉钉响应状态码:", resp.status_code)
        print("钉钉响应内容:", resp.text)
        resp.raise_for_status()
        print("✅ 钉钉推送成功")
    except Exception as e:
        print(f"❌ 钉钉推送失败: {e}")
        print(f"完整请求URL: {url}")
        print(f"完整请求数据: {data}")
