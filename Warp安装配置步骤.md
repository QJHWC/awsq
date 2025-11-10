# Cloudflare Warp 安装和配置详细步骤

## 🎯 目标
让每次注册使用不同的出口IP，避免账号关联。

---

## 📥 第一步：安装 Warp 客户端

### Windows 安装

1. **访问官网下载**
   ```
   https://1.1.1.1/
   ```

2. **点击"下载 Windows 版"**
   - 文件名：`Cloudflare_WARP_Release-x64.msi`
   - 大小：约 150MB

3. **运行安装程序**
   - 双击 `.msi` 文件
   - 点击"下一步"完成安装
   - 安装完成后自动启动

4. **首次启动**
   - 托盘会出现 Cloudflare 图标
   - 点击图标打开控制面板

---

## ⚙️ 第二步：配置 Warp

### 方案一：使用免费版Warp（简单但有限制）

**问题**：免费版Warp **不直接提供SOCKS5代理**

**解决方案A：使用Warp的VPN模式（全局代理）**

1. 打开Warp客户端
2. 点击"连接"按钮
3. 所有流量自动通过Warp

**优点**：
- ✅ 无需配置
- ✅ 全局生效

**缺点**：
- ❌ 影响所有应用
- ❌ 无法单独控制Chrome

**脚本配置**：
```python
# 如果使用全局VPN模式，禁用脚本中的代理配置
WARP_PROXY_ENABLED = False
```

---

### 方案二：使用Warp+ SOCKS5代理（推荐）⭐

**升级到Warp+**（需要购买或邀请获得）：

1. **打开Warp客户端**

2. **进入设置**
   - 点击右上角齿轮图标⚙️
   - 或右键托盘图标 → "首选项"

3. **启用本地代理**
   - 找到"网络"或"Network"设置
   - 启用"Local Proxy"或"本地代理"
   - 设置端口：`40000`（或任意端口）
   - 协议选择：`SOCKS5`

4. **验证代理**
   ```powershell
   # 测试端口是否开放
   Test-NetConnection -ComputerName 127.0.0.1 -Port 40000
   ```

**脚本配置**：
```python
# 在 amazonq_auto_register.py 中
WARP_PROXY_ENABLED = True
WARP_SOCKS5_PROXY = "socks5://127.0.0.1:40000"
```

---

### 方案三：使用第三方工具转换（免费版也可用）

如果不想付费，使用 **Cloudflared** 工具：

#### 安装Cloudflared

1. **下载**
   ```
   https://github.com/cloudflare/cloudflared/releases
   ```
   选择：`cloudflared-windows-amd64.exe`

2. **重命名**
   ```powershell
   Rename-Item cloudflared-windows-amd64.exe cloudflared.exe
   ```

3. **放到系统路径**
   ```powershell
   Move-Item cloudflared.exe C:\Windows\System32\
   ```

#### 启动SOCKS5代理

打开PowerShell，运行：

```powershell
cloudflared access tcp --hostname localhost --url socks5://127.0.0.1:40000
```

**或创建启动脚本** `启动Warp代理.bat`：

```bat
@echo off
chcp 65001 >nul 2>&1

echo.
echo ========================================
echo   启动 Cloudflare Warp SOCKS5 代理
echo ========================================
echo.
echo 代理地址: socks5://127.0.0.1:40000
echo.
echo 按 Ctrl+C 停止代理
echo.
echo ========================================
echo.

cloudflared proxy-dns --port 40000 --address 127.0.0.1

pause
```

**脚本配置**：
```python
WARP_PROXY_ENABLED = True
WARP_SOCKS5_PROXY = "socks5://127.0.0.1:40000"
```

---

### 方案四：临时禁用代理（测试用）

如果暂时不想配置Warp，可以先禁用：

**修改配置**（`amazonq_auto_register.py` 第47行）：
```python
WARP_PROXY_ENABLED = False  # 改为 False
```

注册时会显示：
```
（不使用Warp代理，直接连接）
```

---

## 🧪 第三步：验证配置

### 测试1：检查Warp连接状态

```powershell
# 查看当前IP（不通过Warp）
curl https://api.ipify.org

# 查看通过Warp的IP
curl --proxy socks5://127.0.0.1:40000 https://api.ipify.org
```

两个IP应该不同。

### 测试2：检查端口监听

```powershell
netstat -ano | findstr :40000
```

应该看到端口被监听。

### 测试3：运行注册脚本

```
在浏览器点击：🌐 有头模式
```

终端应显示：
```
  ✓ Warp代理: socks5://127.0.0.1:40000
  💡 每次注册将使用不同的出口IP
```

---

## ❓ 常见问题

### Q1: 免费版Warp够用吗？

**答**：
- ✅ 够用：如果使用VPN模式（全局代理）
- ⚠️ 有限：无SOCKS5，IP轮换较慢
- 💰 推荐：升级Warp+或使用cloudflared工具

### Q2: Warp多久换一次IP？

**答**：
- Warp不保证每次换IP
- 通常每隔几分钟到几小时轮换
- 手动断开重连可能获得新IP
- 每次注册间隔30-60秒可增加轮换概率

### Q3: 没有Warp可以用其他代理吗？

**答**：可以！修改配置：

```python
# 使用其他SOCKS5代理
WARP_SOCKS5_PROXY = "socks5://127.0.0.1:1080"  # 你的代理端口

# 使用HTTP代理
WARP_SOCKS5_PROXY = "http://127.0.0.1:8080"

# 使用远程代理
WARP_SOCKS5_PROXY = "socks5://proxy.example.com:1080"
```

### Q4: 如何手动触发Warp换IP？

**方法一：重启连接**
```powershell
# 如果安装了warp-cli
warp-cli disconnect
timeout /t 2 /nobreak
warp-cli connect
```

**方法二：客户端操作**
- 打开Warp客户端
- 点击"断开"
- 等待2秒
- 点击"连接"

---

## 🎯 推荐配置（按需选择）

### 配置A：最强防护（推荐）

```python
WARP_PROXY_ENABLED = True
WARP_SOCKS5_PROXY = "socks5://127.0.0.1:40000"
```

- ✅ 独立IP
- ✅ 完整反指纹
- ✅ 最低关联风险

### 配置B：简化配置（测试用）

```python
WARP_PROXY_ENABLED = False
```

- ✅ 无需配置Warp
- ✅ 仍有UA+Profile+反指纹保护
- ⚠️ 同一IP可能被关联

### 配置C：自定义代理

```python
WARP_PROXY_ENABLED = True
WARP_SOCKS5_PROXY = "socks5://your-proxy-server:port"
```

- ✅ 使用自己的代理服务
- ✅ 更可控的IP管理

---

## 🚀 快速开始（无需Warp）

如果暂时不想配置Warp，可以直接测试：

### 1. 禁用代理

编辑 `amazonq_auto_register.py` 第47行：
```python
WARP_PROXY_ENABLED = False
```

### 2. 测试注册

点击 **🌐 有头模式**

虽然IP相同，但其他反指纹措施仍然生效：
- ✅ 每次不同的UA
- ✅ 独立Profile
- ✅ Canvas/WebGL随机
- ✅ 硬件信息随机

### 3. 后续添加Warp

配置好Warp后，改回：
```python
WARP_PROXY_ENABLED = True
```

---

## 📌 当前状态

您的配置：
```python
WARP_PROXY_ENABLED = True  # 已启用
WARP_SOCKS5_PROXY = "socks5://127.0.0.1:40000"  # 默认端口
```

**需要做的**：

✅ **选项1（简单）**：禁用Warp代理，先测试其他反指纹功能
```python
WARP_PROXY_ENABLED = False
```

✅ **选项2（完整）**：安装Warp+并配置SOCKS5代理到40000端口

✅ **选项3（免费）**：使用cloudflared工具创建本地SOCKS5代理

---

**建议：先测试反指纹功能（禁用Warp），确认一切正常后再配置Warp！** 🚀

