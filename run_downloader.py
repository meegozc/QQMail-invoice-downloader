#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QQ邮箱发票下载器 - 启动脚本
=============================
功能：
1. 自动加载配置文件
2. 如果配置不完整，提示用户配置
3. 自动设置环境变量
4. 启动主下载脚本

使用方法：
    python run_downloader.py                  # 使用配置文件运行
    python run_downloader.py 260101 260601    # 指定日期范围
    python run_downloader.py auto             # 自动日期范围
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 项目目录
PROJECT_DIR = Path(__file__).parent
CONFIG_FILE = PROJECT_DIR / "config.json"
MAIN_SCRIPT = PROJECT_DIR / "invoice_downloader_v82.py"


def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 配置文件读取失败: {e}")
    return {}


def check_config(config):
    """检查配置是否完整"""
    missing = []
    
    if not config.get('qq_email'):
        missing.append('QQ 邮箱地址')
    if not config.get('qq_password'):
        missing.append('QQ 邮箱授权码')
    
    return missing


def setup_directories(config):
    """设置发票存放目录"""
    storage_dir = config.get('invoice_storage_dir', '')
    
    if not storage_dir:
        # 使用默认目录
        storage_dir = str(PROJECT_DIR / "invoices")
        config['invoice_storage_dir'] = storage_dir
        
        # 保存回配置文件
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    # 创建目录
    Path(storage_dir).mkdir(parents=True, exist_ok=True)
    return storage_dir


def calculate_date_range(config):
    """计算日期范围"""
    date_config = config.get('date_range', {})
    
    if date_config.get('auto', True):
        # 自动模式：从今天往前推 N 天
        days = date_config.get('default_days', 30)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return start_date.strftime('%y%m%d'), end_date.strftime('%y%m%d')
    else:
        # 手动模式：返回 None，让用户指定
        return None, None


def main():
    print("=" * 60)
    print("🚀 QQ邮箱发票下载器 v8.2")
    print("=" * 60)
    
    # 1. 加载配置
    print("\n📋 加载配置文件...")
    config = load_config()
    
    if not config:
        print("❌ 配置文件不存在，请先运行配置向导:")
        print(f"   python setup_config.py")
        sys.exit(1)
    
    # 2. 检查配置
    missing = check_config(config)
    if missing:
        print(f"\n⚠️ 缺少必要配置: {', '.join(missing)}")
        print("\n💡 请运行配置向导:")
        print(f"   python setup_config.py")
        sys.exit(1)
    
    # 3. 设置环境变量
    print("\n⚙️  设置环境变量...")
    os.environ['QQ_EMAIL'] = config['qq_email']
    os.environ['QQ_PASSWORD'] = config['qq_password']
    
    storage_dir = setup_directories(config)
    os.environ['INVOICE_BASE_DIR'] = storage_dir
    
    print(f"   📧 邮箱: {config['qq_email']}")
    print(f"   📁 存放目录: {storage_dir}")
    
    # 4. 处理日期参数
    args = sys.argv[1:]
    
    if len(args) == 0:
        # 没有参数，使用配置的自动模式
        start, end = calculate_date_range(config)
        if start and end:
            print(f"\n📅 自动日期范围: {start} ~ {end}")
            args = [start, end]
        else:
            print("\n⚠️  未指定日期范围，使用默认最近 30 天")
            end = datetime.now().strftime('%y%m%d')
            start = (datetime.now() - timedelta(days=30)).strftime('%y%m%d')
            args = [start, end]
    
    # 5. 启动主脚本
    print(f"\n🚀 启动发票下载器...")
    print(f"   日期范围: {args[0]} ~ {args[1]}\n")
    
    # 使用 subprocess 运行主脚本
    import subprocess
    result = subprocess.run(
        [sys.executable, str(MAIN_SCRIPT)] + args,
        cwd=str(PROJECT_DIR),
        env=os.environ
    )
    
    # 6. 生成统计报表（放在当期目录）
    print("\n" + "=" * 60)
    print("📊 生成统计报表...")
    print("=" * 60)
    
    from datetime import datetime
    today = datetime.now().strftime('%Y%m%d')
    current_dir = Path(storage_dir) / today
    
    if current_dir.exists():
        report_script = PROJECT_DIR / "generate_invoice_report.py"
        subprocess.run(
            [sys.executable, str(report_script), str(current_dir)],
            cwd=str(PROJECT_DIR),
            env=os.environ
        )
        
        # 显示报表位置
        report_files = list(current_dir.glob("发票统计报表_*.xlsx"))
        if report_files:
            latest = max(report_files, key=lambda f: f.stat().st_mtime)
            print(f"\n📁 报表已保存: {latest}")
    else:
        print(f"⚠️  未找到当期目录: {current_dir}")
    
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
