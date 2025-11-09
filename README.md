# Amazon Q to OpenAI API Bridge

将 Amazon Q Developer 转换为 OpenAI 兼容的 API 服务，支持流式和非流式响应。

## ✨ 核心特性

- **OpenAI 兼容接口** - 完全兼容 OpenAI Chat Completions API（`/v1/chat/completions`）
- **账号管理系统** - 支持多账号管理，启用/禁用控制，自动令牌刷新
- **设备授权登录** - 通过 URL 快速登录并自动创建账号（5分钟超时）
- **智能负载均衡** - 从启用的账号中随机选择，实现简单的负载分配
- **API Key 白名单** - 可选的访问控制，支持开发模式
- **现代化前端** - 美观的 Web 控制台，支持账号管理和 Chat 测试
- **自动重试机制** - Token 过期时自动刷新并重试请求

## 🚀 快速开始

### 1. 安装依赖（必需）

```bash
# 创建虚拟环境
python -m venv .venv

# Windows
.venv\Scripts\activate
pip install -r requirements.txt

# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件
# OPENAI_KEYS="key1,key2,key3"  # 可选，留空则为开发模式
```

**配置说明：**
- `OPENAI_KEYS` 为空或未设置：开发模式，不校验 Authorization
- `OPENAI_KEYS` 设置后：仅白名单中的 key 可访问 API
- API Key 仅用于访问控制，不映射到特定账号

### 3. 启动 API 服务

```bash
python -m uvicorn app:app --reload --port 8000
```

访问：
- 🏠 Web 控制台：http://localhost:8000/
- 💚 健康检查：http://localhost:8000/healthz

## 🌐 公网部署

### 方案一：Cloudflare Tunnel 内网穿透（推荐）⭐

**优势**：完全免费 | 无需公网IP | 自动HTTPS | 3分钟部署

**快速开始：**

```bash
# 1. 下载 cloudflared
# Windows: https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
# 重命名为 cloudflared.exe 并放到项目目录

# 2. 配置 API 密钥
双击运行：配置API密钥.bat

# 3. 一键部署
双击运行：一键部署_Cloudflare.bat
```

**获取公网地址：**
```
终端显示：https://abc-def-ghi.trycloudflare.com
这就是你的公网 API 地址！
```

**客户端配置：**
```python
import openai

client = openai.OpenAI(
    base_url="https://abc-def-ghi.trycloudflare.com/v1",
    api_key="sk-790214"  # 你在 .env 中设置的密钥
)

response = client.chat.completions.create(
    model="claude-sonnet-4.5",
    messages=[{"role": "user", "content": "你好"}]
)
```

### 方案二：其他部署方式

详细部署文档：**`部署说明.txt`** 和 **`快速部署指南.txt`**

包含以下方案：
- 🔧 路由器端口转发
- ☁️ 云服务器部署（阿里云/腾讯云/AWS）
- 🐳 Docker 部署
- 🔒 Nginx 反向代理 + HTTPS
- 🌍 Ngrok 内网穿透

## 🤖 自动注册（全新功能）

### 方式一：全自动注册（推荐）⭐

**一键自动注册 Amazon Q 账号！**

```bash
# 单个注册
双击：开始注册.bat

# 批量注册（5个账号）
双击：批量注册.bat

# 或使用命令行
python amazonq_auto_register.py
python 批量注册.py
```

**自动化流程（16步）：**
1. ✅ 自动生成随机邮箱、姓名、密码
2. ✅ Chrome 无痕模式自动化
3. ✅ 自动填写所有表单（逐字符输入）
4. ✅ 自动获取邮箱验证码
5. ✅ 自动完成 AWS 授权
6. ✅ 自动添加账号到数据库

**技术特性：**
- 参考 cursorregester2.0 项目实现
- DrissionPage 4.1+ 无头浏览器自动化
- 邮箱 API 集成（https://mail.qjhvip.top）
- URL 登录流程（设备授权）
- 完全自动化，无需人工干预

**依赖安装：**
```bash
pip install DrissionPage requests
```

### 方式二：Web 控制台 URL 登录

访问 http://localhost:8000/ 使用可视化界面：
1. 找到"URL 登录（5分钟超时）"区域
2. 点击"开始登录"
3. 在浏览器中完成 AWS 登录
4. 点击"等待授权并创建账号"

### 方式三：REST API 手动创建

**创建账号**
```bash
curl -X POST http://localhost:8000/v2/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "label": "我的账号",
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret",
    "refreshToken": "your-refresh-token",
    "enabled": true
  }'
```

**列出所有账号**
```bash
curl http://localhost:8000/v2/accounts
```

**更新账号（切换启用状态）**
```bash
curl -X PATCH http://localhost:8000/v2/accounts/{account_id} \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

**刷新 Token**
```bash
curl -X POST http://localhost:8000/v2/accounts/{account_id}/refresh
```

**删除账号**
```bash
curl -X DELETE http://localhost:8000/v2/accounts/{account_id}
```

### URL 登录（设备授权）

快速添加账号的最简单方式：

1. **启动登录流程**
```bash
curl -X POST http://localhost:8000/v2/auth/start \
  -H "Content-Type: application/json" \
  -d '{"label": "新账号", "enabled": true}'
```

返回：
```json
{
  "authId": "xxx",
  "verificationUriComplete": "https://...",
  "userCode": "ABCD-1234",
  "expiresIn": 600,
  "interval": 1
}
```

2. **在浏览器中打开 `verificationUriComplete` 完成登录**

3. **等待并创建账号**（最多5分钟）
```bash
curl -X POST http://localhost:8000/v2/auth/claim/{authId}
```

成功后自动创建并启用账号。

### OpenAI 兼容 API

#### 非流式请求

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "claude-sonnet-4",
    "stream": false,
    "messages": [
      {"role": "system", "content": "你是一个乐于助人的助手"},
      {"role": "user", "content": "你好，请讲一个简短的故事"}
    ]
  }'
```

#### 流式请求（SSE）

```bash
curl -N -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "claude-sonnet-4",
    "stream": true,
    "messages": [
      {"role": "user", "content": "讲一个笑话"}
    ]
  }'
```

#### Python 示例

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-api-key"  # 如果配置了 OPENAI_KEYS
)

response = client.chat.completions.create(
    model="claude-sonnet-4",
    messages=[
        {"role": "user", "content": "你好"}
    ]
)

print(response.choices[0].message.content)
```

## 🔐 授权与账号选择

### 授权机制
- **开发模式**（`OPENAI_KEYS` 未设置）：不校验 Authorization
- **生产模式**（`OPENAI_KEYS` 已设置）：必须提供白名单中的 key

### 账号选择策略
- 从所有 `enabled=1` 的账号中**随机选择**
- API Key 不映射到特定账号
- 无可用账号时返回 401

### Token 刷新
- 请求时若账号缺少 accessToken，自动刷新
- 上游返回 401/403 时，自动刷新并重试一次
- 可手动调用刷新接口

## 📁 项目结构

```
.
├── app.py                          # FastAPI 主应用
├── auth_flow.py                    # 设备授权登录
├── replicate.py                    # Amazon Q 请求复刻
├── amazonq_auto_register.py        # ⭐ 自动注册脚本
├── 批量注册.py                     # ⭐ 批量注册脚本
├── 开始注册.bat                    # ⭐ 启动单个注册
├── 批量注册.bat                    # ⭐ 启动批量注册
├── requirements.txt                # Python 依赖
├── data.sqlite3                    # SQLite 数据库（自动创建）
├── frontend/
│   └── index.html                  # Web 控制台
├── templates/
│   └── streaming_request.json      # 请求模板
└── screenshots/                    # 自动截图目录
```

## 🛠️ 技术栈

- **后端**: FastAPI + Python 3.8+
- **数据库**: SQLite3
- **前端**: 纯 HTML/CSS/JavaScript
- **认证**: AWS OIDC 设备授权流程

## 🔧 高级配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_KEYS` | API Key 白名单（逗号分隔） | 空（开发模式） |

### 数据库结构

```sql
CREATE TABLE accounts (
    id TEXT PRIMARY KEY,
    label TEXT,
    clientId TEXT,
    clientSecret TEXT,
    refreshToken TEXT,
    accessToken TEXT,
    other TEXT,                    -- JSON 格式的额外信息
    last_refresh_time TEXT,
    last_refresh_status TEXT,
    created_at TEXT,
    updated_at TEXT,
    enabled INTEGER DEFAULT 1      -- 1=启用, 0=禁用
);
```

## 🐛 故障排查

### 401 Unauthorized
- 检查 `OPENAI_KEYS` 配置
- 确认至少有一个 `enabled=1` 的账号
- 验证账号的 clientId/clientSecret/refreshToken 正确

### Token 刷新失败
- 检查网络连接
- 验证 refreshToken 是否过期
- 查看账号的 `last_refresh_status` 字段

### 无响应/超时
- 检查 Amazon Q 服务可达性
- 查看服务日志排查错误

## 📝 API 端点

### 账号管理
- `POST /v2/accounts` - 创建账号
- `GET /v2/accounts` - 列出所有账号
- `GET /v2/accounts/{id}` - 获取账号详情
- `PATCH /v2/accounts/{id}` - 更新账号
- `DELETE /v2/accounts/{id}` - 删除账号
- `POST /v2/accounts/{id}/refresh` - 刷新 Token

### 设备授权
- `POST /v2/auth/start` - 启动登录流程
- `GET /v2/auth/status/{authId}` - 查询登录状态
- `POST /v2/auth/claim/{authId}` - 等待并创建账号

### OpenAI 兼容
- `POST /v1/chat/completions` - Chat Completions API

### 其他
- `GET /` - Web 控制台
- `GET /healthz` - 健康检查

## 📊 完整使用流程

### 场景一：启动账号管理服务

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 API 服务
python -m uvicorn app:app --host 0.0.0.0 --port 8000

# 3. 访问 Web 控制台
浏览器打开：http://localhost:8000
```

### 场景二：全自动注册账号

**方式 A：命令行（推荐）**
```bash
# 安装自动注册依赖
pip install DrissionPage requests

# 单个注册
双击：开始注册.bat
# 或运行：python amazonq_auto_register.py

# 批量注册（5个）
双击：批量注册.bat
# 或运行：python 批量注册.py
```

**方式 B：Web 界面**
1. 访问 http://localhost:8000
2. 找到"⭐ 全自动注册（一键完成）"区域
3. 点击"🚀 启动全自动注册"按钮
4. 等待完成（Chrome 会自动打开并完成注册）

### 场景三：手动 URL 登录

1. 访问 http://localhost:8000
2. 找到"URL 登录（5分钟超时）"
3. 点击"开始登录"
4. 在浏览器中完成登录
5. 点击"等待授权并创建账号"

## 📄 许可证

本项目仅供学习和测试使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！