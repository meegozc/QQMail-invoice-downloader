#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QQ邮箱发票下载器 - 配置管理工具
================================
功能：
1. 交互式配置 QQ 邮箱、授权码、保存目录等
2. 查看当前配置
3. 验证配置是否正确
4. 自动同步到主脚本的环境变量

使用方法：
    python setup_config.py          # 交互式配置
    python setup_config.py --show   # 显示当前配置
    python setup_config.py --test   # 测试邮箱连接
"""

import json
import os
import sys
from pathlib import Path
from imap_tools import MailBox

# 配置文件路径
CONFIG_FILE = Path(__file__).parent / "config.json"

# 默认配置
DEFAULT_CONFIG = {
    "qq_email": "",
    "qq_password": "",
    "invoice_base_dir": "",
    "date_range": {
        "auto": True,
        "default_days": 30
    },
    "browser": {
        "headless": True,
        "timeout": 30
    },
    "logging": {
        "level": "INFO",
        "save_to_file": True
    }
}


def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 合并默认配置（确保新增字段存在）
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
        except json.JSONDecodeError:
            print("⚠️ 配置文件格式错误，使用默认配置")
            return DEFAULT_CONFIG.copy()
    else:
        print("📝 配置文件不存在，创建默认配置")
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    print(f"✅ 配置已保存到: {CONFIG_FILE}")


def mask_password(password):
    """隐藏密码显示"""
    if not password:
        return "(未设置)"
    if len(password) <= 4:
        return "****"
    return password[:2] + "*" * (len(password) - 4) + password[-2:]


def show_config():
    """显示当前配置"""
    config = load_config()
    
    print("\n" + "=" * 60)
    print("📋 当前配置")
    print("=" * 60)
    
    print(f"\n📧 QQ 邮箱: {config.get('qq_email', '(未设置)')}")
    print(f"🔑 授权码: {mask_password(config.get('qq_password', ''))}")
    
    base_dir = config.get('invoice_storage_dir', '')
    if base_dir:
        print(f"📁 存放目录: {base_dir}")
    else:
        print(f"📁 存放目录: (使用默认 - 脚本所在目录/invoices/)")
    
    print(f"\n⚙️  日期范围:")
    date_range = config.get('date_range', {})
    print(f"   - 自动模式: {'✅ 开启' if date_range.get('auto', True) else '❌ 关闭'}")
    print(f"   - 默认天数: {date_range.get('default_days', 30)} 天")
    
    print(f"\n🌐 浏览器:")
    browser = config.get('browser', {})
    print(f"   - 无头模式: {'✅ 开启' if browser.get('headless', True) else '❌ 关闭'}")
    print(f"   - 超时时间: {browser.get('timeout', 30)} 秒")
    
    print(f"\n📊 日志:")
    logging = config.get('logging', {})
    print(f"   - 级别: {logging.get('level', 'INFO')}")
    print(f"   - 保存到文件: {'✅ 是' if logging.get('save_to_file', True) else '❌ 否'}")
    
    print("\n" + "=" * 60)


def setup_interactive():
    """交互式配置向导"""
    print("\n" + "=" * 60)
    print("🔧 QQ邮箱发票下载器 - 配置向导")
    print("=" * 60)
    
    config = load_config()
    
    # 1. QQ 邮箱
    print("\n📧 配置 QQ 邮箱地址")
    current_email = config.get('qq_email', '')
    if current_email:
        print(f"   当前: {current_email}")
    email_input = input(f"   请输入 QQ 邮箱 (回车保持: {current_email}): ").strip()
    if email_input:
        config['qq_email'] = email_input
    elif not current_email:
        print("   ⚠️ 邮箱地址不能为空！")
        email_input = input("   请输入 QQ 邮箱: ").strip()
        config['qq_email'] = email_input
    
    # 2. 授权码
    print("\n🔑 配置 QQ 邮箱授权码")
    print("   💡 获取方式：QQ 邮箱 → 设置 → 账户 → POP3/IMAP 服务 → 生成授权码")
    current_pwd = config.get('qq_password', '')
    if current_pwd:
        print(f"   当前: {mask_password(current_pwd)}")
    pwd_input = input("   请输入授权码 (回车保持): ").strip()
    if pwd_input:
        config['qq_password'] = pwd_input
    elif not current_pwd:
        print("   ⚠️ 授权码不能为空！")
        pwd_input = input("   请输入授权码: ").strip()
        config['qq_password'] = pwd_input
    
    # 3. 发票存放目录
    print("\n📁 配置发票存放目录")
    current_dir = config.get('invoice_storage_dir', '')
    if current_dir:
        print(f"   当前: {current_dir}")
    else:
        default_dir = str(Path(__file__).parent / "invoices")
        print(f"   默认: {default_dir}")
    
    dir_input = input("   请输入存放目录 (回车使用默认): ").strip()
    if dir_input:
        config['invoice_storage_dir'] = dir_input
    elif not current_dir:
        config['invoice_storage_dir'] = str(Path(__file__).parent / "invoices")
    
    # 4. 自动日期范围
    print("\n📅 配置日期范围")
    auto_mode = config.get('date_range', {}).get('auto', True)
    auto_input = input(f"   是否自动计算日期范围？(y/n, 当前: {'y' if auto_mode else 'n'}): ").strip().lower()
    if auto_input in ['y', 'yes']:
        config['date_range']['auto'] = True
    elif auto_input in ['n', 'no']:
        config['date_range']['auto'] = False
    
    if not config['date_range']['auto']:
        days_input = input(f"   默认搜索天数 (当前: {config['date_range'].get('default_days', 30)}): ").strip()
        if days_input.isdigit():
            config['date_range']['default_days'] = int(days_input)
    
    # 保存配置
    print("\n")
    save_config(config)
    
    # 测试连接（可选）
    test = input("\n🔌 是否测试邮箱连接？(y/n): ").strip().lower()
    if test in ['y', 'yes']:
        test_connection(config)
    
    print("\n✅ 配置完成！")
    print(f"\n📂 下次运行发票下载器时，将自动使用这些配置")
    print(f"   运行命令: python invoice_downloader_v82.py")


def test_connection(config):
    """测试邮箱连接"""
    email = config.get('qq_email', '')
    password = config.get('qq_password', '')
    
    if not email or not password:
        print("\n❌ 请先配置邮箱和授权码")
        return
    
    print(f"\n🔌 正在测试连接 {email}...")
    try:
        with MailBox('imap.qq.com').login(email, password) as mailbox:
            # 获取邮件数量
            count = 0
            for _ in mailbox.fetch(limit=1):
                count = 1
                break
            
            if count > 0:
                print(f"✅ 连接成功！邮箱中有邮件")
            else:
                print(f"✅ 连接成功！邮箱为空")
            
            # 显示文件夹
            print("\n📁 邮箱文件夹:")
            for folder in mailbox.folder.list():
                print(f"   - {folder.name}")
    except Exception as e:
        print(f"\n❌ 连接失败: {str(e)}")
        print("\n💡 可能的原因:")
        print("   1. 授权码不正确（注意不是 QQ 密码）")
        print("   2. 未开启 IMAP 服务")
        print("   3. 网络连接问题")


def setup_env_vars():
    """设置环境变量（供主脚本使用）"""
    config = load_config()
    
    # 设置环境变量
    if config.get('qq_email'):
        os.environ['QQ_EMAIL'] = config['qq_email']
    if config.get('qq_password'):
        os.environ['QQ_PASSWORD'] = config['qq_password']
    if config.get('invoice_storage_dir'):
        os.environ['INVOICE_BASE_DIR'] = config['invoice_storage_dir']
    
    return config


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="QQ邮箱发票下载器 - 配置管理")
    parser.add_argument('--show', action='store_true', help='显示当前配置')
    parser.add_argument('--test', action='store_true', help='测试邮箱连接')
    parser.add_argument('--reset', action='store_true', help='重置为默认配置')
    
    args = parser.parse_args()
    
    if args.show:
        show_config()
    elif args.test:
        config = load_config()
        test_connection(config)
    elif args.reset:
        print("🔄 重置配置...")
        save_config(DEFAULT_CONFIG)
        print("✅ 已重置为默认配置")
    else:
        setup_interactive()
