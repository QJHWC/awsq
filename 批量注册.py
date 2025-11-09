# -*- coding: utf-8 -*-
"""
Amazon Q 批量注册脚本
参考 cursorregester2.0 项目
"""

# UTF-8 编码
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

import time
from pathlib import Path

# 导入主注册函数
from amazonq_auto_register import auto_register


def batch_register(count=5, delay=15):
    """
    批量注册 Amazon Q 账号
    
    Args:
        count: 注册数量
        delay: 每个账号间隔时间（秒）
    """
    print("="*70)
    print(" "*15 + "Amazon Q 批量自动注册")
    print("="*70)
    print(f"\n配置：")
    print(f"  注册数量: {count} 个")
    print(f"  间隔时间: {delay} 秒")
    print(f"  Chrome 无痕模式")
    print(f"  URL 登录流程")
    print("\n" + "="*70)
    
    success_count = 0
    failed_count = 0
    
    for i in range(count):
        print(f"\n{'#'*70}")
        print(f"#  开始注册第 {i+1}/{count} 个账号")
        print(f"{'#'*70}")
        
        try:
            result = auto_register()
            
            if result:
                success_count += 1
                print(f"\n✅ 第 {i+1} 个账号注册成功")
            else:
                failed_count += 1
                print(f"\n❌ 第 {i+1} 个账号注册失败")
        
        except KeyboardInterrupt:
            print(f"\n\n⚠ 用户中断")
            break
        
        except Exception as e:
            failed_count += 1
            print(f"\n❌ 第 {i+1} 个账号异常: {str(e)}")
        
        # 间隔
        if i < count - 1:
            print(f"\n等待 {delay} 秒后继续...")
            time.sleep(delay)
    
    # 统计
    print(f"\n{'='*70}")
    print(" "*20 + "批量注册完成")
    print(f"{'='*70}")
    print(f"  总数: {count}")
    print(f"  成功: {success_count}")
    print(f"  失败: {failed_count}")
    print(f"  成功率: {success_count/count*100:.1f}%")
    print(f"{'='*70}")


if __name__ == '__main__':
    print("\n输入注册数量（默认5）: ", end='')
    try:
        count_input = input().strip()
        count = int(count_input) if count_input else 5
    except:
        count = 5
    
    batch_register(count=count, delay=15)

