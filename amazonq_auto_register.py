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
    
    # 步骤 3: 初始化 Chrome 无痕模式
    print("\n【步骤 3】初始化 Chrome 无痕模式")
    print("-"*70)
    
    co = ChromiumOptions()
    
    # 设置 Chrome 路径
    if os.path.exists(CHROME_PATH):
        co.set_browser_path(CHROME_PATH)
        print(f"  ✓ Chrome 路径: {CHROME_PATH}")
    
    # 无痕模式（参考 cursor 项目）
    co.set_argument('--incognito')
    co.set_argument('--window-size=1280,900')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_pref('excludeSwitches', ['enable-automation'])
    co.set_pref('useAutomationExtension', False)
    
    print("  ✓ 无痕模式已配置")
    
    page = ChromiumPage(addr_or_opts=co)
    page.set.timeouts(base=10, page_load=30)
    
    print("  ✓ 浏览器已启动")
    
    try:
        # 步骤 4: 打开验证链接
        print("\n【步骤 4】打开 AWS 验证链接")
        print("-"*70)
        page.get(verification_url)
        time.sleep(2)
        
        # 等待页面稳定（页面可能会快速跳转）
        print("  ✓ 等待页面加载和跳转...")
        time.sleep(3)
        
        save_screenshot(page, "01_opened")
        current_url = page.url
        print(f"  ✓ 页面已加载")
        print(f"    当前 URL: {current_url[:60]}...")
        
        # 步骤 5: 点击确认按钮（第一个页面）
        print("\n【步骤 5】查找并点击 'Confirm and continue' 按钮")
        print("-"*70)
        
        # 尝试查找确认按钮
        confirm_button = None
        try:
            buttons = page.eles('tag:button', timeout=3)
            for btn in buttons:
                try:
                    btn_text = (btn.text or '').lower()
                    if 'confirm' in btn_text and btn.states.is_displayed:
                        confirm_button = btn
                        print(f"  ✓ 找到按钮: '{btn.text}'")
                        break
                except:
                    continue
        except:
            pass
        
        if confirm_button:
            print("  ✓ 正在点击...")
            # 使用 JavaScript 点击（参考 cursor 项目，避免 NoRectError）
            try:
                page.run_js("arguments[0].click();", confirm_button)
                print("  ✓ 按钮已点击（JavaScript 方式）")
            except:
                confirm_button.click()
                print("  ✓ 按钮已点击（直接点击）")
            
            time.sleep(4)
            save_screenshot(page, "02_after_confirm")
        else:
            print("  ⚠ 未找到确认按钮（可能已经跳转到登录页）")
        
        # 步骤 6: 填写邮箱（参考 cursor 项目的逻辑）
        print("\n【步骤 6】填写邮箱")
        print("-"*70)
        
        time.sleep(2)
        current_url = page.url
        print(f"  当前 URL: {current_url[:60]}...")
        
        # 查找邮箱输入框（参考 cursor 项目，增加更多选择器）
        email_input = None
        email_selectors = [
            'xpath://input[@placeholder="username@example.com"]',
            'xpath://input[@type="email"]',
            'xpath://input[@type="text"]',
            '@placeholder=username@example.com',
            '@type=email',
            '@type=text',
            'tag:input',
        ]
        
        for selector in email_selectors:
            try:
                if selector.startswith('xpath:') or selector.startswith('tag:'):
                    inputs = page.eles(selector, timeout=2)
                    for inp in inputs:
                        try:
                            # 检查输入框类型和占位符
                            inp_type = inp.attr('type') or ''
                            inp_placeholder = (inp.attr('placeholder') or '').lower()
                            
                            if inp_type in ['email', 'text'] and ('email' in inp_placeholder or 'username' in inp_placeholder or 'example' in inp_placeholder):
                                email_input = inp
                                print(f"  ✓ 找到邮箱输入框: {selector}")
                                break
                        except:
                            continue
                else:
                    email_input = page.ele(selector, timeout=2)
                    if email_input:
                        print(f"  ✓ 找到邮箱输入框: {selector}")
                        break
            except:
                continue
            
            if email_input:
                break
        
        if email_input:
            print(f"  ✓ 找到邮箱输入框")
            print(f"  ✓ 正在输入: {email}")
            
            # 逐字符输入（模拟真人打字）
            email_input.click()
            time.sleep(0.3)
            email_input.clear()
            time.sleep(0.5)
            
            # 逐字符输入邮箱
            for char in email:
                email_input.input(char, clear=False)
                time.sleep(0.05)  # 模拟打字速度
            
            time.sleep(1)
            save_screenshot(page, "03_email_filled")
            print(f"  ✓ 邮箱已填写完成")
        else:
            print("  ✗ 未找到邮箱输入框")
            save_screenshot(page, "error_no_email_input")
            return False
        
        # 步骤 7: 点击第一个继续按钮
        print("\n【步骤 7】点击继续按钮（第1次）")
        print("-"*70)
        
        # 查找继续按钮（参考 cursor 项目）
        continue_btn = None
        try:
            # 使用 xpath 查找包含"继续"的按钮
            continue_btn = page.ele('xpath://button[contains(., "继续")]', timeout=3)
        except:
            try:
                # 备用：查找 submit 类型的按钮
                buttons = page.eles('button[type=submit]', timeout=2)
                if buttons:
                    continue_btn = buttons[0]
            except:
                pass
        
        if continue_btn:
            print(f"  ✓ 找到按钮: '{continue_btn.text}'")
            print("  ✓ 正在点击...")
            
            # 使用 JavaScript 点击（避免 NoRectError）
            try:
                page.run_js("arguments[0].click();", continue_btn)
                print("  ✓ 按钮已点击（JavaScript 方式）")
            except:
                continue_btn.click()
                print("  ✓ 按钮已点击")
            
            time.sleep(4)
            save_screenshot(page, "04_after_email_continue")
        else:
            print("  ✗ 未找到继续按钮")
        
        # 步骤 8: 填写姓名
        print("\n【步骤 8】填写姓名")
        print("-"*70)
        
        time.sleep(2)
        current_url = page.url
        print(f"  当前 URL: {current_url[:60]}...")
        
        # 查找姓名输入框
        name_input = None
        try:
            # 尝试多种可能的选择器
            name_selectors = [
                'xpath://input[@placeholder="Maria José Silva"]',
                'xpath://input[@name="name"]',
                'xpath://input[@type="text"]',
                '@name=name',
                '@type=text',
            ]
            
            for selector in name_selectors:
                try:
                    if selector.startswith('xpath:'):
                        inputs = page.eles(selector, timeout=2)
                        if inputs:
                            name_input = inputs[0]
                            print(f"  ✓ 找到姓名输入框: {selector}")
                            break
                    else:
                        name_input = page.ele(selector, timeout=2)
                        if name_input:
                            print(f"  ✓ 找到姓名输入框: {selector}")
                            break
                except:
                    continue
        except:
            pass
        
        if name_input:
            print(f"  ✓ 正在输入姓名: {full_name}")
            
            # 逐字符输入（模拟真人打字）
            name_input.click()
            time.sleep(0.3)
            name_input.clear()
            time.sleep(0.5)
            
            # 逐字符输入姓名
            for char in full_name:
                name_input.input(char, clear=False)
                time.sleep(0.08)  # 稍慢一点，模拟打字
            
            time.sleep(1)
            save_screenshot(page, "05_name_filled")
            print(f"  ✓ 姓名已填写完成")
        else:
            print("  ⚠ 未找到姓名输入框（可能不需要）")
        
        # 步骤 9: 点击第二个继续按钮
        print("\n【步骤 9】点击继续按钮（第2次）")
        print("-"*70)
        
        # 再次查找继续按钮
        continue_btn2 = None
        try:
            continue_btn2 = page.ele('xpath://button[contains(., "继续")]', timeout=3)
        except:
            try:
                # 尝试查找 Continue 按钮
                continue_btn2 = page.ele('xpath://button[contains(., "Continue")]', timeout=2)
            except:
                try:
                    buttons = page.eles('button[type=submit]', timeout=2)
                    if buttons:
                        continue_btn2 = buttons[0]
                except:
                    pass
        
        if continue_btn2:
            print(f"  ✓ 找到按钮: '{continue_btn2.text}'")
            print("  ✓ 正在点击...")
            
            # 使用 JavaScript 点击（避免 NoRectError）
            page.run_js("arguments[0].click();", continue_btn2)
            print("  ✓ 按钮已点击")
            
            time.sleep(5)
            save_screenshot(page, "06_after_name")
        else:
            print("  ✗ 未找到继续按钮")
        
        # 步骤 10: 获取并填写验证码
        print("\n【步骤 10】获取邮箱验证码")
        print("-"*70)
        
        time.sleep(2)
        current_url = page.url
        print(f"  当前 URL: {current_url[:60]}...")
        
        # 检查是否是验证码页面
        page_html = page.html
        if '验证' in page_html or 'verify' in page_html.lower() or '6位' in page_html:
            print("  ✓ 检测到验证码页面")
            
            # 调用邮箱 API 获取验证码
            print(f"  ✓ 正在从邮箱 API 获取验证码...")
            print(f"    邮箱: {email}")
            
            verification_code = None
            max_attempts = 12  # 最多尝试12次（60秒）
            
            for attempt in range(max_attempts):
                print(f"    尝试 {attempt + 1}/{max_attempts}...")
                
                try:
                    # 调用邮箱 API
                    api_url = f'{EMAIL_API_BASE_URL}?mailbox={email}&admin_token={EMAIL_API_TOKEN}'
                    response = requests.get(api_url, timeout=10)
                    
                    if response.status_code == 200:
                        emails = response.json()
                        
                        # 查找 AWS 相关的邮件
                        for email_data in emails:
                            subject = email_data.get('subject', '').lower()
                            sender = email_data.get('sender', '').lower()
                            
                            if 'aws' in subject or 'aws' in sender or 'amazon' in subject:
                                # 获取验证码
                                code = email_data.get('verification_code', '')
                                if not code:
                                    # 尝试从邮件正文提取
                                    body = email_data.get('body', '') or email_data.get('text', '')
                                    import re
                                    match = re.search(r'\b(\d{6})\b', body)
                                    if match:
                                        code = match.group(1)
                                
                                if code:
                                    verification_code = code
                                    print(f"    ✓ 找到验证码: {verification_code}")
                                    break
                    
                    if verification_code:
                        break
                    
                    # 等待5秒后重试
                    if attempt < max_attempts - 1:
                        time.sleep(5)
                
                except Exception as e:
                    print(f"    ⚠ API 请求失败: {str(e)}")
                    time.sleep(5)
            
            if not verification_code:
                print("  ✗ 未获取到验证码")
                print("  ⚠ 请手动输入验证码")
                save_screenshot(page, "waiting_for_code")
                
                # 保持浏览器打开让用户手动输入
                print("\n  浏览器将保持打开 60 秒供手动输入验证码...")
                time.sleep(60)
                return False
            
            # 填写验证码
            print(f"\n  ✓ 正在填写验证码: {verification_code}")
            
            # 查找验证码输入框
            code_input = None
            try:
                # 尝试多种选择器
                code_selectors = [
                    'xpath://input[@placeholder="6 位数"]',
                    '@placeholder=6 位数',
                    '@type=text',
                    'xpath://input[@type="text"]',
                ]
                
                for selector in code_selectors:
                    try:
                        if selector.startswith('xpath:'):
                            inputs = page.eles(selector, timeout=2)
                            if inputs:
                                code_input = inputs[0]
                                print(f"  ✓ 找到验证码输入框: {selector}")
                                break
                        else:
                            code_input = page.ele(selector, timeout=2)
                            if code_input:
                                print(f"  ✓ 找到验证码输入框: {selector}")
                                break
                    except:
                        continue
            except:
                pass
            
            if code_input:
                # 填写验证码（逐字符输入）
                print(f"  ✓ 正在填写验证码: {verification_code}")
                
                code_input.click()
                time.sleep(0.3)
                code_input.clear()
                time.sleep(0.5)
                
                # 逐字符输入验证码
                for char in verification_code:
                    code_input.input(char, clear=False)
                    time.sleep(0.1)  # 验证码输入稍慢
                
                time.sleep(1)
                save_screenshot(page, "07_code_filled")
                print(f"  ✓ 验证码已填写完成: {verification_code}")
                
                # 点击 Continue 按钮
                print("\n【步骤 11】点击 Continue 按钮")
                print("-"*70)
                
                continue_btn3 = None
                try:
                    continue_btn3 = page.ele('xpath://button[contains(., "Continue")]', timeout=3)
                except:
                    try:
                        buttons = page.eles('button[type=submit]', timeout=2)
                        if buttons:
                            continue_btn3 = buttons[0]
                    except:
                        pass
                
                if continue_btn3:
                    print(f"  ✓ 找到按钮: '{continue_btn3.text}'")
                    print("  ✓ 正在点击...")
                    
                    # JavaScript 点击
                    page.run_js("arguments[0].click();", continue_btn3)
                    print("  ✓ 按钮已点击")
                    
                    time.sleep(5)
                    save_screenshot(page, "08_after_code_submit")
                else:
                    print("  ✗ 未找到 Continue 按钮")
            else:
                print("  ✗ 未找到验证码输入框")
        else:
            print("  ⚠ 非验证码页面，跳过此步骤")
        
        # 步骤 12: 设置密码
        print("\n【步骤 12】设置密码")
        print("-"*70)
        
        time.sleep(2)
        current_url = page.url
        page_html = page.html
        print(f"  当前 URL: {current_url[:60]}...")
        
        # 检查是否是密码设置页面
        if 'password' in page_html.lower() or '密码' in page_html:
            print("  ✓ 检测到密码设置页面")
            print(f"  ✓ 使用密码: {password}")
            
            # 查找密码输入框（必须找到两个）
            password_inputs = []
            
            # 直接查找所有 type=password 的输入框
            try:
                password_inputs = page.eles('@type=password', timeout=3)
                if password_inputs:
                    print(f"  ✓ 找到 {len(password_inputs)} 个密码输入框")
                    
                    # 显示每个输入框的占位符
                    for idx, inp in enumerate(password_inputs):
                        placeholder = inp.attr('placeholder') or '无占位符'
                        print(f"    {idx+1}. {placeholder}")
            except:
                print("  ✗ 未找到密码输入框")
                
            # 备用方法
            if not password_inputs:
                try:
                    password_inputs = page.eles('xpath://input[@type="password"]', timeout=2)
                    if password_inputs:
                        print(f"  ✓ (备用方法) 找到 {len(password_inputs)} 个密码输入框")
                except:
                    pass
            
            if len(password_inputs) >= 2:
                print(f"\n  ✓ 开始填写 2 个密码框")
                print(f"  使用密码: {password}")
                print("-"*70)
                
                # 填写第一个密码框（密码）
                print(f"  [1/2] 填写第一个密码框（密码）...")
                try:
                    password_inputs[0].click()  # 先点击聚焦
                    time.sleep(0.3)
                    password_inputs[0].clear()
                    time.sleep(0.5)
                    
                    # 逐字符输入（更可靠）
                    for char in password:
                        password_inputs[0].input(char, clear=False)
                        time.sleep(0.05)  # 模拟打字速度
                    
                    time.sleep(0.8)
                    print(f"      ✓ 第一个密码框已填写")
                except Exception as e:
                    print(f"      ✗ 填写失败: {e}")
                
                # 填写第二个密码框（确认密码）
                print(f"  [2/2] 填写第二个密码框（确认密码）...")
                try:
                    password_inputs[1].click()  # 先点击聚焦
                    time.sleep(0.3)
                    password_inputs[1].clear()
                    time.sleep(0.5)
                    
                    # 逐字符输入
                    for char in password:
                        password_inputs[1].input(char, clear=False)
                        time.sleep(0.05)
                    
                    time.sleep(0.8)
                    print(f"      ✓ 第二个密码框已填写")
                except Exception as e:
                    print(f"      ✗ 填写失败: {e}")
                
                time.sleep(1)
                save_screenshot(page, "09_both_passwords_filled")
                print(f"\n  ✓ 两个密码框都已填写完成！")
                print("-"*70)
                
                # 点击继续按钮
                print("\n【步骤 12.1】点击继续按钮（提交密码）")
                print("-"*70)
                
                continue_btn_pwd = None
                
                # 多种选择器（兼容中英文）
                continue_selectors = [
                    'xpath://button[contains(., "继续")]',        # 中文
                    'xpath://button[contains(., "Continue")]',  # 英文
                    'xpath://button[contains(., "Next")]',      # 英文
                    'xpath://button[contains(., "提交")]',       # 中文
                    'xpath://button[contains(., "Submit")]',    # 英文
                    'button[type=submit]',
                    '@type=submit',
                ]
                
                for selector in continue_selectors:
                    try:
                        if selector.startswith('xpath:'):
                            buttons = page.eles(selector, timeout=2)
                            for btn in buttons:
                                try:
                                    if btn.states.is_displayed:
                                        continue_btn_pwd = btn
                                        print(f"  ✓ 找到按钮: '{btn.text}' (selector: {selector})")
                                        break
                                except:
                                    continue
                        else:
                            btn = page.ele(selector, timeout=2)
                            if btn:
                                continue_btn_pwd = btn
                                print(f"  ✓ 找到按钮: '{btn.text}' (selector: {selector})")
                                break
                    except:
                        continue
                    
                    if continue_btn_pwd:
                        break
                
                if continue_btn_pwd:
                    print(f"  ✓ 找到按钮: '{continue_btn_pwd.text}'")
                    print("  ✓ 正在点击...")
                    
                    # JavaScript 点击
                    page.run_js("arguments[0].click();", continue_btn_pwd)
                    print("  ✓ 按钮已点击")
                    
                    time.sleep(5)
                    save_screenshot(page, "10_after_password")
                else:
                    print("  ✗ 未找到继续按钮（可能不需要或已自动跳转）")
            elif len(password_inputs) == 1:
                print("  ⚠ 只找到1个密码框，可能不需要确认密码")
                password_inputs[0].clear()
                time.sleep(0.5)
                password_inputs[0].input(password)
                print(f"  ✓ 密码已填写")
                save_screenshot(page, "09_password_filled")
            else:
                print("  ✗ 未找到密码输入框")
        else:
            print("  ⚠ 非密码页面，跳过此步骤")
        
        # 步骤 13: 检查并点击最终授权确认（无论前面如何都要执行）
        print("\n【步骤 13】查找并点击最终授权确认")
        print("-"*70)
        
        time.sleep(3)
        current_url = page.url
        page_html = page.html
        print(f"  当前 URL: {current_url[:60]}...")
        
        save_screenshot(page, "12_before_final_confirm")
        
        # 检查是否是 Authorization requested 页面
        if 'Authorization requested' in page_html or 'Confirm this code' in page_html:
            print("  ✓ 检测到最终授权确认页面！")
            
            # 显示用户代码
            import re
            code_match = re.search(r'([A-Z0-9]{4}-[A-Z0-9]{4})', page_html)
            if code_match:
                print(f"  ✓ 用户代码: {code_match.group(1)}")
            
            # 查找并点击 "Confirm and continue" 按钮
            print("  ✓ 正在查找 'Confirm and continue' 按钮...")
            
            final_confirm_btn = None
            
            # 多种选择器查找（按优先级）
            final_selectors = [
                'xpath://button[contains(text(), "Confirm and continue")]',
                'xpath://button[contains(text(), "Confirm")]',
                'xpath://button[contains(., "确认并继续")]',
                'xpath://button[contains(., "确认")]',
                'button[type=submit]',
            ]
            
            for selector in final_selectors:
                try:
                    if selector.startswith('xpath:'):
                        buttons = page.eles(selector, timeout=3)
                        if buttons:
                            for btn in buttons:
                                try:
                                    btn_text = (btn.text or '').strip()
                                    if btn.states.is_displayed:
                                        final_confirm_btn = btn
                                        print(f"    ✓ 找到按钮: '{btn_text}' ({selector})")
                                        break
                                except:
                                    continue
                    else:
                        btn = page.ele(selector, timeout=3)
                        if btn and btn.states.is_displayed:
                            final_confirm_btn = btn
                            print(f"    ✓ 找到按钮: '{btn.text}' ({selector})")
                except:
                    continue
                
                if final_confirm_btn:
                    break
            
            # 如果还是找不到，列出所有按钮
            if not final_confirm_btn:
                print("  ⚠ 未找到确认按钮，列出所有按钮...")
                try:
                    all_btns = page.eles('tag:button', timeout=3)
                    for idx, btn in enumerate(all_btns):
                        btn_text = (btn.text or '').strip()
                        print(f"    {idx+1}. '{btn_text}'")
                        
                        # 尝试找包含 confirm 的任何按钮
                        if 'confirm' in btn_text.lower() and btn.states.is_displayed:
                            final_confirm_btn = btn
                            print(f"    → 选择此按钮")
                            break
                except:
                    pass
            
            if final_confirm_btn:
                print(f"\n  ✓✓✓ 找到最终确认按钮: '{final_confirm_btn.text}'")
                print("  ✓✓✓ 正在点击最终确认按钮...")
                
                # 使用 JavaScript 点击（最可靠）
                try:
                    page.run_js("arguments[0].click();", final_confirm_btn)
                    print("  ✓✓✓ 最终确认按钮已点击！（JavaScript）")
                except Exception as e1:
                    print(f"  ⚠ JS点击失败: {e1}，尝试直接点击...")
                    try:
                        final_confirm_btn.click()
                        print("  ✓✓✓ 最终确认按钮已点击！（直接点击）")
                    except Exception as e2:
                        print(f"  ✗ 所有点击方法都失败: {e2}")
                
                time.sleep(5)
                save_screenshot(page, "13_final_confirm_clicked")
                
                # 步骤 13.1: 点击 "Allow access" 按钮（授权应用访问）
                print("\n【步骤 13.1】点击 'Allow access' 按钮（授权应用）")
                print("-"*70)
                
                time.sleep(3)
                current_url = page.url
                page_html = page.html
                print(f"  当前 URL: {current_url[:60]}...")
                
                save_screenshot(page, "14_before_allow_access")
                
                # 检查是否是 "Allow access" 页面
                if 'Allow Amazon Q Developer' in page_html or 'Allow access' in page_html:
                    print("  ✓ 检测到应用授权页面！")
                    
                    # 查找 "Allow access" 按钮
                    print("  ✓ 正在查找 'Allow access' 按钮...")
                    
                    allow_btn = None
                    
                    # 多种选择器
                    allow_selectors = [
                        'xpath://button[contains(text(), "Allow access")]',
                        'xpath://button[contains(., "Allow access")]',
                        'xpath://button[contains(., "允许访问")]',
                        'xpath://button[contains(., "Allow")]',
                    ]
                    
                    for selector in allow_selectors:
                        try:
                            buttons = page.eles(selector, timeout=3)
                            if buttons:
                                for btn in buttons:
                                    try:
                                        btn_text = (btn.text or '').strip()
                                        if btn.states.is_displayed and 'allow' in btn_text.lower():
                                            allow_btn = btn
                                            print(f"    ✓ 找到按钮: '{btn_text}'")
                                            break
                                    except:
                                        continue
                        except:
                            continue
                        
                        if allow_btn:
                            break
                    
                    # 如果还没找到，列出所有按钮
                    if not allow_btn:
                        print("  ⚠ 使用备用方法查找...")
                        try:
                            all_btns = page.eles('tag:button', timeout=3)
                            print(f"  页面上共有 {len(all_btns)} 个按钮:")
                            for idx, btn in enumerate(all_btns):
                                btn_text = (btn.text or '').strip()
                                print(f"    {idx+1}. '{btn_text}'")
                                
                                if 'allow' in btn_text.lower() and btn.states.is_displayed:
                                    allow_btn = btn
                                    print(f"    → 选择此按钮")
                                    break
                        except:
                            pass
                    
                    if allow_btn:
                        print(f"\n  ✓✓✓ 找到 'Allow access' 按钮: '{allow_btn.text}'")
                        print("  ✓✓✓ 正在点击授权按钮...")
                        
                        # JavaScript 点击
                        try:
                            page.run_js("arguments[0].click();", allow_btn)
                            print("  ✓✓✓ 授权按钮已点击！（JavaScript）")
                        except Exception as e1:
                            print(f"  ⚠ JS点击失败: {e1}，尝试直接点击...")
                            try:
                                allow_btn.click()
                                print("  ✓✓✓ 授权按钮已点击！（直接点击）")
                            except Exception as e2:
                                print(f"  ✗ 点击失败: {e2}")
                        
                        time.sleep(5)
                        save_screenshot(page, "15_allow_access_clicked")
                    else:
                        print("  ✗ 未找到 'Allow access' 按钮")
                        save_screenshot(page, "error_no_allow_button")
                else:
                    print("  ⚠ 非应用授权页面，跳过")
            else:
                print("  ✗✗✗ 未找到最终确认按钮！")
                save_screenshot(page, "error_no_final_confirm_button")
        else:
            print("  ⚠ 非授权确认页面")
            
            # 即使不是标准页面，也尝试查找 Confirm 按钮
            print("  ⚠ 尝试查找任何 Confirm 按钮...")
            try:
                all_btns = page.eles('tag:button', timeout=3)
                for btn in all_btns:
                    btn_text = (btn.text or '').lower()
                    if 'confirm' in btn_text and btn.states.is_displayed:
                        print(f"  ✓ 找到 Confirm 按钮: '{btn.text}'，尝试点击...")
                        page.run_js("arguments[0].click();", btn)
                        time.sleep(3)
                        save_screenshot(page, "13_confirm_clicked_fallback")
                        break
            except:
                pass
        
        # 步骤 14: 检查最终状态
        print("\n【步骤 14】检查最终授权状态")
        print("-"*70)
        
        time.sleep(3)
        final_url = page.url
        final_html = page.html
        
        print(f"  最终 URL: {final_url[:60]}...")
        
        # 检查是否成功
        if 'approved' in final_html.lower():
            print("  ✓ 检测到授权成功！")
            save_screenshot(page, "07_success")
        else:
            print("  ⚠ 未检测到成功标志，请手动完成剩余步骤")
            save_screenshot(page, "07_current_state")
        
        # 保持浏览器打开
        print("\n" + "="*70)
        print("  浏览器将保持打开 30 秒，请检查状态")
        print("  如果看到 'Request approved'，说明授权成功！")
        print("="*70)
        
        time.sleep(30)
        
    except Exception as e:
        print(f"\n✗ 发生错误: {str(e)}")
        save_screenshot(page, "error")
        import traceback
        traceback.print_exc()
    
    finally:
        page.quit()
        print("\n  ✓ 浏览器已关闭")
    
    # 步骤 15: 创建账号
    print("\n【步骤 15】创建 Amazon Q 账号")
    print("-"*70)
    print("  正在调用 /v2/auth/claim 接口（URL 登录流程）...")
    
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
                print(f"  Has Token: {bool(account.get('accessToken'))}")
                print("="*70)
                
                # 验证账号
                print("\n【验证】查询账号列表")
                response2 = requests.get(f'{LOCAL_API_BASE}/v2/accounts')
                if response2.status_code == 200:
                    accounts = response2.json()
                    print(f"  ✓ 当前共有 {len(accounts)} 个账号")
                    
                    for acc in accounts:
                        if acc.get('label') == email:
                            print(f"  ✓ 新账号已添加到数据库")
                            break
                
                return True
            else:
                print(f"  ✗ 授权状态: {result.get('status')}")
                print(f"  ✗ 错误: {result.get('error')}")
                return False
        else:
            print(f"  ✗ API 错误: {response.status_code}")
            print(f"  {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        print("  ✗ 超时（5分钟）")
        return False
    except Exception as e:
        print(f"  ✗ 错误: {str(e)}")
        return False


# ==================== 主程序 ====================
if __name__ == '__main__':
    print("\n提示：")
    print("  - 确保 API 服务正在运行 (localhost:8000)")
    print("  - 确保已安装 Google Chrome")
    print("  - 使用 URL 登录（设备授权）流程")
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
        print("  ⚠ 注册未完全成功")
        print("\n  请检查：")
        print("    1. screenshots/ 目录的截图")
        print("    2. 浏览器中是否完成了所有步骤")
        print("    3. API 服务是否正常")
    print("="*70)

