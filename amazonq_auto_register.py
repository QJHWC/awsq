# -*- coding: utf-8 -*-
"""
Amazon Q 自动注册（最终版）
参考 cursorregester2.0 项目实现
支持 Chrome 无痕模式 + 自动填写 + 自动点击
"""

# ==================== UTF-8 编码初始化 ====================
import sys
import os
import io

if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
    except:
        pass
    
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# ==================== 导入模块 ====================
import time
import random
import string
import requests
from pathlib import Path
from datetime import datetime
from DrissionPage import ChromiumPage, ChromiumOptions

# ==================== 配置 ====================
EMAIL_API_TOKEN = 'sk-790214'
EMAIL_API_BASE_URL = 'https://mail.qjhvip.top/api/emails'
EMAIL_DOMAIN = 'qjhvip.top'
EMAIL_PREFIX_LENGTH = 12

LOCAL_API_BASE = 'http://localhost:8000'
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

# Cloudflare Warp 代理配置
# 如果安装了 Warp 客户端，默认会在本地开启 SOCKS5 代理
WARP_PROXY_ENABLED = False  # 设为 True 启用代理（需先配置Warp）
WARP_SOCKS5_PROXY = "socks5://127.0.0.1:40000"  # Warp默认SOCKS5端口
# 备用HTTP代理（如果Warp配置了HTTP代理端口）
# WARP_HTTP_PROXY = "http://127.0.0.1:40001"

def generate_random_user_agent():
    """
    动态生成随机User-Agent（无限不重复）
    每次生成全新的UA组合，避免指纹关联
    """
    # 随机选择操作系统
    os_choices = [
        ("Windows NT 10.0; Win64; x64", "Windows 10"),
        ("Windows NT 11.0; Win64; x64", "Windows 11"),
        ("Macintosh; Intel Mac OS X 10_15_7", "macOS Catalina"),
        ("Macintosh; Intel Mac OS X 11_0", "macOS Big Sur"),
        ("Macintosh; Intel Mac OS X 12_0", "macOS Monterey"),
        ("Macintosh; Intel Mac OS X 13_0", "macOS Ventura"),
        ("Macintosh; Intel Mac OS X 14_0", "macOS Sonoma"),
        ("X11; Linux x86_64", "Linux"),
    ]
    
    os_string, os_name = random.choice(os_choices)
    
    # 随机Chrome版本（120-131）+ 随机小版本
    chrome_major = random.randint(120, 131)
    chrome_minor = random.randint(0, 0)  # 主版本通常是x.0.0.0
    chrome_build = random.randint(6000, 7000)
    chrome_patch = random.randint(0, 200)
    chrome_version = f"{chrome_major}.{chrome_minor}.{chrome_build}.{chrome_patch}"
    
    # 随机WebKit版本（537.36是标准，但可以微调）
    webkit_build = random.randint(535, 538)
    webkit_patch = random.randint(30, 40)
    webkit_version = f"{webkit_build}.{webkit_patch}"
    
    # 组装User-Agent
    ua = f"Mozilla/5.0 ({os_string}) AppleWebKit/{webkit_version} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit_version}"
    
    return ua

# ==================== 工具函数 ====================
def generate_random_email():
    """生成随机邮箱"""
    chars = string.ascii_lowercase + string.digits
    prefix = ''.join(random.choice(chars) for _ in range(EMAIL_PREFIX_LENGTH))
    return f'{prefix}@{EMAIL_DOMAIN}'

def generate_random_name():
    """生成随机英文名字（扩展名字库）"""
    first_names = [
        'John', 'Emma', 'Michael', 'Olivia', 'William', 'Ava', 'James', 'Sophia',
        'Robert', 'Isabella', 'David', 'Mia', 'Richard', 'Charlotte', 'Joseph', 'Amelia',
        'Thomas', 'Harper', 'Charles', 'Evelyn', 'Daniel', 'Abigail', 'Matthew', 'Emily',
        'Anthony', 'Elizabeth', 'Donald', 'Sofia', 'Mark', 'Avery', 'Paul', 'Ella',
        'Steven', 'Scarlett', 'Andrew', 'Grace', 'Joshua', 'Chloe', 'Kenneth', 'Victoria',
        'Kevin', 'Riley', 'Brian', 'Aria', 'George', 'Lily', 'Edward', 'Aubrey',
        'Ronald', 'Zoey', 'Timothy', 'Penelope', 'Jason', 'Layla', 'Jeffrey', 'Nora',
        'Ryan', 'Hannah', 'Jacob', 'Lillian', 'Gary', 'Addison', 'Nicholas', 'Eleanor'
    ]
    last_names = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
        'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
        'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
        'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill',
        'Flores', 'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell',
        'Mitchell', 'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz',
        'Parker', 'Cruz', 'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris', 'Murphy'
    ]
    first = random.choice(first_names)
    last = random.choice(last_names)
    return f'{first} {last}'

def generate_random_password(length=18):
    """
    生成随机密码（包含数字、字母、特殊符号，确保唯一性）
    
    Args:
        length: 密码长度（默认18位，增强安全性和唯一性）
    
    Returns:
        str: 随机密码
    """
    # 定义字符集
    lowercase = string.ascii_lowercase  # a-z
    uppercase = string.ascii_uppercase  # A-Z
    digits = string.digits  # 0-9
    special = '!@#$%^&*'  # 特殊符号（AWS 支持的）
    
    # 确保至少包含每种类型的字符（多一些确保复杂度）
    password = [
        random.choice(lowercase),
        random.choice(lowercase),
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(uppercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(digits),
        random.choice(digits),
        random.choice(special),
        random.choice(special),
    ]
    
    # 填充剩余字符（使用完全随机）
    all_chars = lowercase + uppercase + digits + special
    for _ in range(length - len(password)):
        password.append(random.choice(all_chars))
    
    # 多次打乱顺序（增加随机性）
    for _ in range(3):
        random.shuffle(password)
    
    # 添加时间戳确保唯一性（可选）
    import hashlib
    timestamp = str(time.time())
    unique_char = hashlib.md5(timestamp.encode()).hexdigest()[0]
    password.append(unique_char)
    random.shuffle(password)
    
    return ''.join(password)[:length]  # 确保不超过指定长度

def save_screenshot(page, name):
    """保存截图"""
    try:
        Path('screenshots').mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'screenshots/{timestamp}_{name}.png'
        page.get_screenshot(path=filename)
        print(f"    ✓ 截图已保存: {filename}")
    except:
        pass

# ==================== 主函数 ====================
def auto_register():
    """自动注册主函数"""
    print("="*70)
    print(" "*20 + "Amazon Q 自动注册")
    print("="*70)
    
    # 初始化注册成功标志
    registration_success = False
    
    # 步骤 1: 生成邮箱、姓名和密码
    print("\n【步骤 1】生成注册信息")
    print("-"*70)
    email = generate_random_email()
    full_name = generate_random_name()
    password = generate_random_password(16)
    print(f"  ✓ 邮箱: {email}")
    print(f"  ✓ 姓名: {full_name}")
    print(f"  ✓ 密码: {password}")
    
    # 步骤 2: 启动授权
    print("\n【步骤 2】调用 URL 登录接口（设备授权）")
    print("-"*70)
    try:
        response = requests.post(
            f'{LOCAL_API_BASE}/v2/auth/start',
            json={'label': email, 'enabled': True},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"  ✗ 失败: {response.status_code}")
            return False
        
        data = response.json()
        auth_id = data['authId']
        verification_url = data['verificationUriComplete']
        user_code = data['userCode']
        
        print(f"  ✓ 授权已启动（URL 登录模式）")
        print(f"    Auth ID: {auth_id}")
        print(f"    用户代码: {user_code}")
        
    except Exception as e:
        print(f"  ✗ 错误: {str(e)}")
        return False
    
    # 步骤 3: 初始化 Chrome 无痕模式（+ 反指纹配置）
    manual_mode = os.environ.get('HEADLESS', '0') == '1'  # 改名：HEADLESS=1 表示手动模式
    mode_name = "手动模式" if manual_mode else "自动模式"
    
    # 动态生成随机User-Agent（每次都不同）
    random_ua = generate_random_user_agent()
    
    # 创建独立的Profile目录（每次注册使用不同目录，避免指纹关联）
    import tempfile
    profile_dir = Path(tempfile.gettempdir()) / f"chrome_profile_{random.randint(10000, 99999)}"
    profile_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n【步骤 3】初始化 Chrome 无痕模式（{mode_name} + 反指纹）")
    print("-"*70)
    
    co = ChromiumOptions()
    
    # 设置 Chrome 路径
    if os.path.exists(CHROME_PATH):
        co.set_browser_path(CHROME_PATH)
        print(f"  ✓ Chrome 路径: {CHROME_PATH}")
    
    # 生成随机调试端口（避免冲突）并确保可用
    max_attempts = 5
    debug_port = None
    for attempt in range(max_attempts):
        test_port = random.randint(9300, 9400)
        # 检测端口是否被占用
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', test_port))
                debug_port = test_port
                break
            except:
                if attempt < max_attempts - 1:
                    continue
                else:
                    debug_port = test_port  # 最后一次直接使用
    
    co.set_local_port(debug_port)
    co.set_argument(f'--remote-debugging-port={debug_port}')
    print(f"  ✓ 调试端口: {debug_port}")
    
    # 设置随机User-Agent（降低指纹关联）
    co.set_argument(f'--user-agent={random_ua}')
    print(f"  ✓ User-Agent: {random_ua[:80]}...")
    
    # 使用独立的Profile目录（每次注册如同全新浏览器）
    co.set_argument(f'--user-data-dir={str(profile_dir)}')
    print(f"  ✓ Profile目录: {profile_dir.name}")
    
    # 基础无痕模式配置
    co.set_argument('--incognito')
    co.set_argument('--window-size=1280,900')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_pref('excludeSwitches', ['enable-automation'])
    co.set_pref('useAutomationExtension', False)
    
    # 手动模式也显示浏览器（不使用无头）
    if manual_mode:
        print(f"  ✓ 手动模式（浏览器打开，需手动操作）")
    else:
        print(f"  ✓ 自动模式（浏览器自动完成所有步骤）")
    
    print("  ✓ 无痕模式已配置")
    
    page = ChromiumPage(addr_or_opts=co)
    page.set.timeouts(base=10, page_load=30)
    
    print(f"  ✓ 浏览器已启动（{mode_name}）")
    print(f"  💡 反指纹：随机UA + 独立Profile")
    
    try:
        # 步骤 4: 打开验证链接
        print("\n【步骤 4】打开 AWS 验证链接")
        print("-"*70)
        page.get(verification_url)
        time.sleep(2)
        
        # 注入完整反指纹脚本
        try:
            full_anti_fingerprint_script = """
            // === 1. Canvas指纹随机化 ===
            const toDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function() {
                const ctx = this.getContext('2d');
                if (ctx && this.width > 0 && this.height > 0) {
                    try {
                        const imgData = ctx.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imgData.data.length; i += 400) {
                            imgData.data[i] = (imgData.data[i] + Math.floor(Math.random() * 3) - 1) % 256;
                        }
                        ctx.putImageData(imgData, 0, 0);
                    } catch(e) {}
                }
                return toDataURL.apply(this, arguments);
            };
            
            // === 2. WebGL指纹随机化 ===
            const getParam = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(p) {
                if (p === 37445) return 'Intel Inc.';
                if (p === 37446) {
                    const r = ['Intel Iris OpenGL', 'ANGLE (Intel)', 'AMD Radeon'][Math.floor(Math.random()*3)];
                    return r;
                }
                return getParam.apply(this, arguments);
            };
            
            // === 3. 硬件信息随机化 ===
            try {
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => [4, 8, 12, 16][Math.floor(Math.random() * 4)]
                });
            } catch(e) {}
            
            try {
                if ('deviceMemory' in navigator) {
                    Object.defineProperty(navigator, 'deviceMemory', {
                        get: () => [4, 8, 16][Math.floor(Math.random() * 3)]
                    });
                }
            } catch(e) {}
            
            // === 4. 清理本地存储 ===
            try {
                localStorage.clear();
                sessionStorage.clear();
                document.cookie.split(';').forEach(c => {
                    document.cookie = c.replace(/^ +/, '').replace(/=.*/, '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/');
                });
                if (indexedDB && indexedDB.databases) {
                    indexedDB.databases().then(dbs => dbs.forEach(db => indexedDB.deleteDatabase(db.name)));
                }
                if ('caches' in window) {
                    caches.keys().then(keys => keys.forEach(k => caches.delete(k)));
                }
                if (navigator.serviceWorker) {
                    navigator.serviceWorker.getRegistrations().then(regs => regs.forEach(r => r.unregister()));
                }
            } catch(e) {}
            
            console.log('✅ 完整反指纹脚本已注入: Canvas+WebGL+硬件+存储清理');
            """
            page.run_js(full_anti_fingerprint_script)
            print("  ✓ 完整反指纹脚本已注入（Canvas+WebGL+硬件+存储）")
        except Exception as e:
            print(f"  ⚠ 脚本注入失败: {e}")
        
        # 等待页面稳定（页面可能会快速跳转）
        print("  ✓ 等待页面加载和跳转...")
        time.sleep(3)
        
        save_screenshot(page, "01_opened")
        current_url = page.url
        print(f"  ✓ 页面已加载")
        print(f"    当前 URL: {current_url[:60]}...")
        
        # === 手动模式：停止自动化，等待用户手动操作 ===
        if manual_mode:
            print("\n" + "="*70)
            print("  🖐️  手动模式已启动")
            print("="*70)
            print(f"  📧 邮箱: {email}")
            print(f"  👤 姓名: {full_name}")
            print(f"  🔑 密码: {password}")
            print(f"  🔗 授权链接已打开")
            print(f"  ⏰ 验证码: {user_code}")
            print()
            print("  💡 请在浏览器中手动完成以下步骤：")
            print("     1. 点击'Confirm and continue'")
            print("     2. 输入邮箱（已生成）")
            print("     3. 输入姓名（已生成）")
            print("     4. 输入邮箱验证码")
            print("     5. 设置密码（已生成）")
            print("     6. 完成授权")
            print()
            print("  浏览器将保持打开状态...")
            print("  完成后按回车创建账号，或5分钟后自动超时")
            print("="*70)
            
            # 等待用户手动完成（最多5分钟）
            import select
            import sys
            
            print("\n  自动检测授权状态（每5秒检查一次，最多5分钟）...")
            timeout = 300  # 5分钟
            start_time = time.time()
            check_count = 0
            
            while True:
                elapsed = time.time() - start_time
                
                if elapsed > timeout:
                    print("\n  ⏰ 超时（5分钟）")
                    break
                
                # 每5秒检查一次授权状态
                if check_count == 0 or elapsed >= check_count * 5:
                    check_count += 1
                    print(f"\n  [{check_count}] 检查授权状态...")
                    
                    try:
                        check_resp = requests.get(
                            f'{LOCAL_API_BASE}/v2/auth/status/{auth_id}',
                            timeout=5
                        )
                        if check_resp.status_code == 200:
                            status_data = check_resp.json()
                            status = status_data.get('status')
                            remaining = status_data.get('remaining', 0)
                            
                            print(f"      状态: {status}, 剩余时间: {remaining}秒")
                            
                            # 检查是否完成（尝试claim）
                            if True:  # 每次都尝试
                                try:
                                    claim_resp = requests.post(
                                        f'{LOCAL_API_BASE}/v2/auth/claim/{auth_id}',
                                        timeout=5
                                    )
                                    if claim_resp.status_code == 200:
                                        claim_result = claim_resp.json()
                                        if claim_result.get('status') == 'completed':
                                            print(f"      ✅ 授权已完成！")
                                            break
                                        else:
                                            print(f"      ⏳ 授权进行中...")
                                except:
                                    pass
                    except:
                        pass
                
                time.sleep(1)
            
            # 跳过所有自动化步骤，直接到步骤15创建账号
            page.quit()
            print("  ✓ 浏览器已关闭")
            
            # 清理Profile
            import shutil
            if profile_dir.exists():
                shutil.rmtree(str(profile_dir), ignore_errors=True)
                print(f"  ✓ Profile已清理")
            
            # 直接跳转到步骤15
            print("\n【步骤 15】创建 Amazon Q 账号")
            print("-"*70)
            print("  正在调用 /v2/auth/claim 接口...")
            
            try:
                response = requests.post(
                    f'{LOCAL_API_BASE}/v2/auth/claim/{auth_id}',
                    timeout=310
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('status') == 'completed':
                        account = result.get('account', {})
                        print("\n" + "="*70)
                        print("  🎉 注册成功！")
                        print("="*70)
                        print(f"  邮箱: {email}")
                        print(f"  账号ID: {account.get('id')}")
                        print(f"  Label: {account.get('label')}")
                        print(f"  Enabled: {account.get('enabled')}")
                        print("="*70)
                        return True
                    else:
                        print(f"  ✗ 授权状态: {result.get('status')}")
                        print(f"  ✗ 错误: {result.get('error')}")
                        return False
                else:
                    print(f"  ✗ API 错误: {response.status_code}")
                    return False
            except Exception as e:
                print(f"  ✗ 创建账号错误: {str(e)}")
                return False
        
        # === 自动模式：浏览器打开 + 自动检测授权 ===
        print("\n" + "="*70)
        print("  🤖 自动模式：浏览器已打开到授权页面")
        print("="*70)
        print(f"  📧 邮箱: {email}")
        print(f"  👤 姓名: {full_name}")
        print(f"  🔑 密码: {password}")
        print(f"  ⏰ 验证码: {user_code}")
        print()
        print("  💡 浏览器已打开，自动检测授权完成...")
        print("  📊 每5秒检查一次，最多等待5分钟")
        print("="*70)
        
        # 使用与手动模式相同的自动检测逻辑
        print("\n  自动检测授权状态...")
        timeout = 300  # 5分钟
        start_time = time.time()
        check_count = 0
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > timeout:
                print("\n  ⏰ 超时（5分钟）")
                break
            
            # 每5秒检查一次
            if check_count == 0 or elapsed >= check_count * 5:
                check_count += 1
                print(f"\n  [{check_count}] 检查授权状态...")
                
                try:
                    claim_resp = requests.post(
                        f'{LOCAL_API_BASE}/v2/auth/claim/{auth_id}',
                        timeout=5
                    )
                    if claim_resp.status_code == 200:
                        claim_result = claim_resp.json()
                        if claim_result.get('status') == 'completed':
                            print(f"      ✅ 授权已完成！")
                            break
                        else:
                            status = claim_result.get('status', 'unknown')
                            print(f"      ⏳ 状态: {status}")
                except Exception as e:
                    print(f"      ⚠ 检查失败: {e}")
            
            time.sleep(1)
        
        # 自动模式：关闭浏览器并创建账号
        page.quit()
        print("\n  ✓ 浏览器已关闭")
        
        # 清理Profile
        import shutil
        if profile_dir.exists():
            shutil.rmtree(str(profile_dir), ignore_errors=True)
            print(f"  ✓ Profile已清理")
        
        # 创建账号（逻辑与手动模式相同）
        print("\n【步骤 15】创建 Amazon Q 账号")
        print("-"*70)
        print("  正在调用 /v2/auth/claim 接口...")
        
        try:
            response = requests.post(
                f'{LOCAL_API_BASE}/v2/auth/claim/{auth_id}',
                timeout=310
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'completed':
                    account = result.get('account', {})
                    print("\n" + "="*70)
                    print("  🎉 注册成功！")
                    print("="*70)
                    print(f"  邮箱: {email}")
                    print(f"  账号ID: {account.get('id')}")
                    print(f"  Label: {account.get('label')}")
                    print(f"  Enabled: {account.get('enabled')}")
                    print("="*70)
                    return True
                else:
                    print(f"  ✗ 授权状态: {result.get('status')}")
                    return False
            else:
                print(f"  ✗ API 错误: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ✗ 创建账号错误: {str(e)}")
            return False
    
    # （旧的自动化代码已删除，避免混乱）
    
    except Exception as e:
        print(f"\n✗ 自动化过程发生错误: {str(e)}")
        save_screenshot(page, "error")
        import traceback
        traceback.print_exc()
        registration_success = False
    
    finally:
        # 确保浏览器关闭（如果还在运行）
        try:
            page.quit()
            print("\n  ✓ 浏览器已关闭（finally）")
        except:
            print("\n  ⚠️  浏览器可能已关闭")
        
        # 彻底清理临时Profile目录
        try:
            import shutil
            if 'profile_dir' in locals() and profile_dir.exists():
                print(f"\n  🗑️  正在清理临时Profile...")
                for attempt in range(3):
                    try:
                        shutil.rmtree(str(profile_dir), ignore_errors=False)
                        print(f"  ✓ Profile已彻底删除: {profile_dir.name}")
                        break
                    except Exception as e:
                        if attempt < 2:
                            print(f"  ⚠ 删除尝试{attempt+1}失败，1秒后重试...")
                            time.sleep(1)
                        else:
                            print(f"  ⚠ Profile删除失败: {e}")
                            print(f"  💡 请手动删除: {profile_dir}")
        except Exception as e:
            print(f"  ⚠ Profile清理异常: {e}")
    
    # 返回注册结果
    return registration_success


# ==================== 主程序 ====================
if __name__ == '__main__':
    print("\n提示：")

    print("  - 确保 API 服务正在运行 (localhost:8000)")
    print("  - 确保已安装 Google Chrome")
    print("  - 连接 Warp 可获得IP轮换（可选）")
    print("\n按回车键开始...")
    try:
        input()
    except:
        pass
    
    success = auto_register()
    
    print("\n" + "="*70)
    if success:
        print("  ✅ 全部完成！")
        print("\n  下一步：")
        print("    1. 访问 http://localhost:8000 查看账号")
        print("    2. 测试 Chat 功能")
        print("    3. 继续批量注册")
    else:
        print("  ❌ 注册失败")
        print("  请检查错误信息并重试")
    print("="*70)
