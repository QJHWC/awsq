# -*- coding: utf-8 -*-
"""
账号健康检查守护进程
功能：每60秒检测一次所有启用的账号，自动删除被封禁（黑号）的账号
"""
import sqlite3
import time
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# 配置
DB_PATH = Path(__file__).parent / "data.sqlite3"
CHECK_INTERVAL = 60  # 检查间隔（秒）
TEST_MESSAGE = [{"role": "user", "content": "test"}]  # 测试消息

# AWS API配置
AWS_CHAT_URL = "https://qchat.aws.amazon.com/api/2023-11-27/conversations"

def get_conn():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def test_account_health(access_token):
    """
    测试账号是否健康
    返回: (is_healthy, error_reason)
    """
    try:
        # 构造最小测试请求
        payload = {
            "conversationState": {
                "currentMessage": {"userInputMessage": {"content": "test"}},
                "chatTriggerType": "MANUAL"
            }
        }
        
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {access_token}",
            "x-amzn-codewhisperer-optout": "true"
        }
        
        # 发送测试请求（不流式，快速失败）
        resp = requests.post(
            AWS_CHAT_URL, 
            headers=headers, 
            json=payload,
            timeout=(5, 10)  # 连接5秒，读取10秒
        )
        
        # 检查响应
        if resp.status_code == 200:
            return True, None
        
        # 解析错误
        try:
            err = resp.json()
            reason = err.get('reason', '')
            error_type = err.get('__type', '')
            
            # 检测是否被暂停/封禁
            if 'SUSPENDED' in reason or 'SUSPENDED' in error_type:
                return False, f"账号被暂停: {reason}"
            elif resp.status_code in [401, 403]:
                return False, f"认证失败或无权限: {resp.status_code}"
            else:
                return False, f"其他错误: {resp.status_code} - {reason}"
                
        except:
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
            
    except requests.Timeout:
        return False, "请求超时"
    except Exception as e:
        return False, f"异常: {str(e)}"

def delete_account(conn, account_id, reason):
    """删除账号"""
    cursor = conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
    conn.commit()
    return cursor.rowcount > 0

def check_all_accounts():
    """检查所有账号并删除黑号"""
    print(f"\n{'='*80}")
    print(f"账号健康检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    with get_conn() as conn:
        # 获取所有启用的账号
        rows = conn.execute(
            "SELECT id, label, accessToken FROM accounts WHERE enabled=1"
        ).fetchall()
        
        if not rows:
            print("⚠️  没有启用的账号")
            return
        
        print(f"📊 检测 {len(rows)} 个启用的账号...\n")
        
        deleted_count = 0
        healthy_count = 0
        
        for row in rows:
            acc_id = row['id']
            label = row['label'] or acc_id[:20]
            access_token = row['accessToken']
            
            print(f"🔍 检测: {label}...")
            
            if not access_token:
                print(f"   ⚠️  跳过（无access token）\n")
                continue
            
            # 测试账号健康度
            is_healthy, error_reason = test_account_health(access_token)
            
            if is_healthy:
                print(f"   ✅ 健康\n")
                healthy_count += 1
            else:
                print(f"   ❌ 检测到黑号: {error_reason}")
                
                # 删除黑号
                if delete_account(conn, acc_id, error_reason):
                    print(f"   🗑️  已从数据库删除\n")
                    deleted_count += 1
                else:
                    print(f"   ⚠️  删除失败\n")
        
        # 汇总
        print(f"{'='*80}")
        print(f"✅ 健康账号: {healthy_count}")
        print(f"❌ 删除黑号: {deleted_count}")
        print(f"{'='*80}\n")

def main():
    """主循环"""
    print("\n" + "="*80)
    print("🛡️  账号健康检查守护进程已启动")
    print("="*80)
    print(f"⏱️  检查间隔: {CHECK_INTERVAL} 秒")
    print(f"🗑️  自动删除被封禁账号")
    print(f"💡 按 Ctrl+C 停止\n")
    
    try:
        check_count = 0
        while True:
            check_count += 1
            print(f"\n🔄 第 {check_count} 轮检查")
            check_all_accounts()
            
            print(f"⏸️  等待 {CHECK_INTERVAL} 秒后进行下一轮检查...")
            print(f"   （按 Ctrl+C 停止守护进程）\n")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("🛑 守护进程已停止")
        print("="*80)
        sys.exit(0)

if __name__ == "__main__":
    main()

