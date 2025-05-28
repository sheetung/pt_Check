### 🛠 使用方法

#### 1. 安装依赖

```
bash


复制编辑
pip install -r requirements.txt
```

> `requirements.txt` 内容：

```
nginx复制编辑requests
beautifulsoup4
```

#### 2. 设置环境变量

你可以通过 `.env` 文件、系统环境变量，或 GitHub Actions `secrets` 设置以下变量：

| 环境变量名        | 说明                                              |
| ----------------- | ------------------------------------------------- |
| `PTLOVER_COOKIES` | 多账号 Cookie，多个账号使用 `&` 分隔              |
| `BARK_PUSH`       | Bark 推送地址，例如：https://api.day.app/your_key |
| `BARK_SOUND`      | Bark 推送音效（可选）                             |
| `DD_BOT_TOKEN`    | 钉钉机器人 token                                  |
| `DD_BOT_SECRET`   | 钉钉机器人加签密钥（可选，使用加签需提供）        |



------

### 📦 示例

```
bash


复制编辑
python ptlover_checkin.py
```

------

### ⏱ 定时执行（可选）

- 本地可使用 `crontab` 定时
- GitHub Actions 可设置每天定时签到（示例工作流文件见 `.github/workflows/`）

------

## 📢 免责声明

> 请务必阅读以下内容再使用本项目。

- 本脚本仅供学习和研究 Python 网络请求、自动化操作等用途使用。
- 本项目**不对因使用本脚本带来的封号、账号异常、网站访问问题等后果承担任何责任**。
- 使用本脚本即代表你已了解并同意遵守 [PTlover.cc](https://www.ptlover.cc) 的相关使用条款与规定。
- 请**合理设置请求频率**，勿恶意请求网站，避免对 PTlover 服务造成影响。
- 如果你是网站管理者并认为本项目不当使用了您的服务，请联系我立即删除相关内容。