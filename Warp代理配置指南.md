# Cloudflare Warp 代理配置指南

## 🎯 目标

通过 Cloudflare Warp 实现每次注册使用不同的出口IP，配合反指纹措施，大幅降低账号关联风险。

---

## 📥 安装 Cloudflare Warp

### Windows

1. 下载 Warp 客户端：https://1.1.1.1/
2. 安装并启动
3. 注册账号（免费）
4. 连接Warp

### 配置 SOCKS5 代理

Warp默认不开启SOCKS5代理，需要手动启用：

#### 方法一：使用Warp+（推荐）

升级到Warp+后，在设置中启用本地代理：
- 端口：`40000`（SOCKS5）

#### 方法二：使用第三方工具转换

如果免费版Warp不支持SOCKS5，可以使用工具转换：

**使用 CloudflareWarpProxy**：
```bash
# 下载并运行
# https://github.com/cloudflare/cloudflared
cloudflared proxy-dns --port 53 --address 127.0.0.1
```

**或使用 warp-cli（企业版）**：
```bash
warp-cli mode proxy
warp-cli proxy port 40000
```

---

## ⚙️ 配置脚本使用Warp

### 当前配置（amazonq_auto_register.py）

```python
# Cloudflare Warp 代理配置
WARP_PROXY_ENABLED = True  # 启用/禁用
WARP_SOCKS5_PROXY = "socks5://127.0.0.1:40000"  # 端口号
```

### 修改端口（如果不同）

如果您的Warp使用不同端口，修改配置：

```python
# HTTP代理
WARP_SOCKS5_PROXY = "http://127.0.0.1:8080"

# 或其他SOCKS5端口
WARP_SOCKS5_PROXY = "socks5://127.0.0.1:1080"
```

### 禁用代理（直连）

如果暂时不想使用代理：

```python
WARP_PROXY_ENABLED = False
```

---

## 🧪 验证配置

### 1. 测试Warp是否运行

```powershell
# Windows
Test-NetConnection -ComputerName 127.0.0.1 -Port 40000
```

### 2. 测试出口IP

不使用Warp时：
```powershell
curl https://api.ipify.org
```

使用Warp时：
```powershell
curl --proxy socks5://127.0.0.1:40000 https://api.ipify.org
```

应该看到不同的IP地址。

### 3. 测试注册脚本

启动有头模式，观察终端输出：
```
  ✓ Warp代理: socks5://127.0.0.1:40000
  💡 每次注册将使用不同的出口IP
```

---

## 🔄 IP轮换机制

### Cloudflare Warp的IP轮换

Warp **不会每次请求都换IP**，但会：
- 每隔一段时间轮换出口节点
- 重新连接时可能分配新IP
- 使用不同的出口边缘节点

### 手动触发IP更换

**方法一：重启Warp连接**
```powershell
# Windows（需要Warp CLI）
warp-cli disconnect
warp-cli connect
```

**方法二：在脚本中添加延迟**

每次注册间隔30-60秒，让Warp有机会轮换节点。

**方法三：使用Warp Team/Enterprise**

企业版支持更精细的控制和更快的轮换。

---

## 🛡️ 完整的反指纹配置总结

当前脚本已实现的防护措施：

### ✅ 网络层
- [x] Warp代理（IP轮换）
- [x] SOCKS5支持

### ✅ 浏览器层
- [x] 随机User-Agent（动态生成，无限不重复）
- [x] 独立Profile目录（每次全新）
- [x] 随机窗口分辨率
- [x] 语言和地区配置（zh-CN）

### ✅ JavaScript层
- [x] Canvas 指纹随机化（微噪声）
- [x] WebGL 渲染器随机化
- [x] hardwareConcurrency 随机化（4/8/12/16核）
- [x] deviceMemory 随机化（4/8/16GB）
- [x] localStorage/sessionStorage 清理
- [x] IndexedDB 清理
- [x] Cache API 清理
- [x] Service Worker 清理
- [x] Cookies 清理

### ✅ 反自动化检测
- [x] 禁用AutomationControlled特征
- [x] 禁用扩展和插件
- [x] WebRTC IP泄露防护
- [x] GPU软件渲染（避免GPU指纹）

### ✅ 清理机制
- [x] Profile目录自动删除（3次重试）
- [x] 浏览器自动关闭
- [x] 临时文件清理

---

## 🚀 使用流程

### 步骤1：启动Warp

确保Warp客户端正在运行并已连接。

### 步骤2：启动服务

```
双击：启动本地测试服务.bat
```

### 步骤3：注册账号

浏览器访问：`http://localhost:8000`

点击：**🌐 有头模式（可见浏览器）**

每次注册都会：
1. ✅ 生成全新的UA
2. ✅ 创建独立Profile
3. ✅ 通过Warp使用不同IP
4. ✅ 注入反指纹脚本
5. ✅ 完成后删除Profile

---

## 📊 效果验证

### 查看出口IP

在注册过程中，打开浏览器的开发者工具（F12），在Console中执行：

```js
fetch('https://api.ipify.org?format=json')
  .then(r => r.json())
  .then(d => console.log('当前出口IP:', d.ip))
```

每次注册应该看到不同的IP（如果Warp已轮换）。

### 查看指纹

访问：https://abrahamjuliot.github.io/creepjs/

查看Canvas、WebGL、字体等指纹，每次应该不同。

---

## ⚠️ 注意事项

### 1. Warp免费版限制

- 流量有限制（但一般够用）
- IP轮换不如付费代理池频繁
- 如需更频繁轮换，考虑：
  - Warp+ 或 Team 版本
  - 第三方住宅代理池
  - 多个Warp账号轮换

### 2. 合规使用

- 仅用于合法测试和开发
- 遵守AWS服务条款
- 不要用于恶意目的

### 3. 性能影响

- 代理会增加延迟
- Canvas注入可能略微降低渲染性能
- Profile删除需要额外时间

---

## 🔧 故障排查

### 问题：代理连接失败

```
Error: SOCKS5 proxy connection failed
```

**解决**：
1. 确认Warp正在运行
2. 检查端口号是否正确
3. 尝试禁用防火墙
4. 检查Warp设置中是否启用了本地代理

### 问题：IP没有变化

**解决**：
1. 重启Warp连接
2. 等待更长时间再注册
3. 检查是否真的通过代理（访问 https://api.ipify.org）

### 问题：Profile删除失败

```
⚠ Profile删除失败（可能被占用）
```

**解决**：
1. 确保浏览器已完全关闭
2. 手动删除提示的目录
3. 重启电脑释放文件句柄

---

## 📈 批量注册建议

如果需要批量注册多个账号：

1. **使用无头模式**（更快）
2. **每次注册间隔30-60秒**（给Warp时间轮换IP）
3. **监控账号健康**（使用"检测黑号"功能）
4. **分批注册**（不要一次注册太多）

---

## 🌟 最佳实践

### 单账号注册（测试）
```
有头模式 + Warp代理 + 所有反指纹措施
```

### 批量注册（生产）
```
无头模式 + Warp代理 + 30秒间隔 + 健康检测
```

### 指纹验证
```
每次注册前访问指纹检测网站验证配置
```

---

**配置完成后，每次注册都如同来自完全不同的设备和网络！** 🎉

---

**创建时间**：2025-11-10
**版本**：v1.0

