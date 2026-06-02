#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票处理全能工具 - 一键完成下载、提取、分类、报表
=====================================================
功能：
1. 下载发票邮件
2. 提取 PDF 发票信息
3. 智能分类
4. 生成统计报表

使用方法：
    python invoice_toolkit.py              # 全流程（下载+提取+报表）
    python invoice_toolkit.py --extract    # 仅提取和报表
    python invoice_toolkit.py --report     # 仅生成报表
    python invoice_toolkit.py 260101 260601  # 指定日期下载
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# 项目目录
PROJECT_DIR = Path(__file__).parent
CONFIG_FILE = PROJECT_DIR / "config.json"


def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def run_download(date_range=None):
    """运行发票下载"""
    print("\n" + "=" * 60)
    print("📥 步骤 1: 下载发票邮件")
    print("=" * 60)
    
    config = load_config()
    
    # 设置环境变量
    os.environ['QQ_EMAIL'] = config.get('qq_email', '')
    os.environ['QQ_PASSWORD'] = config.get('qq_password', '')
    
    base_dir = config.get('invoice_base_dir', str(PROJECT_DIR / "invoices"))
    os.environ['INVOICE_BASE_DIR'] = base_dir
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    
    # 确定日期范围
    if date_range:
        args = date_range
    else:
        date_config = config.get('date_range', {})
        if date_config.get('auto', True):
            days = date_config.get('default_days', 30)
            end = datetime.now().strftime('%y%m%d')
            start = (datetime.now() - timedelta(days=days)).strftime('%y%m%d')
            args = [start, end]
        else:
            args = None
    
    if not args:
        print("⚠️  未指定日期范围，跳过下载")
        return base_dir
    
    # 运行下载脚本
    main_script = PROJECT_DIR / "invoice_downloader_v82.py"
    result = subprocess.run(
        [sys.executable, str(main_script)] + args,
        cwd=str(PROJECT_DIR),
        env=os.environ
    )
    
    if result.returncode != 0:
        print(f"⚠️  下载失败（退出码: {result.returncode}）")
    
    return base_dir


def run_extract_and_report(invoice_dir=None):
    """运行提取和报表生成"""
    print("\n" + "=" * 60)
    print("📊 步骤 2: 提取发票信息并生成报表")
    print("=" * 60)
    
    if invoice_dir is None:
        config = load_config()
        invoice_dir = config.get('invoice_base_dir', str(PROJECT_DIR / "invoices"))
    
    # 运行报表生成脚本
    report_script = PROJECT_DIR / "generate_invoice_report.py"
    result = subprocess.run(
        [sys.executable, str(report_script), invoice_dir],
        cwd=str(PROJECT_DIR),
        env=os.environ
    )
    
    if result.returncode != 0:
        print(f"⚠️  报表生成失败（退出码: {result.returncode}）")
        return None
    
    # 查找最新生成的报表
    report_files = list(Path(invoice_dir).glob("发票统计报表_*.xlsx"))
    if report_files:
        latest = max(report_files, key=lambda f: f.stat().st_mtime)
        return str(latest)
    return None


def show_summary(invoice_dir=None):
    """显示处理摘要"""
    if invoice_dir is None:
        config = load_config()
        invoice_dir = config.get('invoice_base_dir', str(PROJECT_DIR / "invoices"))
    
    print("\n" + "=" * 60)
    print("📋 处理摘要")
    print("=" * 60)
    
    # 统计 PDF 数量
    pdf_files = list(Path(invoice_dir).glob("**/*.pdf"))
    print(f"📄 发票文件: {len(pdf_files)} 个")
    
    # 统计 Excel 报表
    excel_files = list(Path(invoice_dir).glob("发票统计报表_*.xlsx"))
    if excel_files:
        latest = max(excel_files, key=lambda f: f.stat().st_mtime)
        print(f"📊 最新报表: {latest.name}")
        print(f"   生成时间: {datetime.fromtimestamp(latest.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 显示分类统计（如果有报表数据）
    if excel_files:
        print(f"\n📁 发票目录: {invoice_dir}")


def main():
    print("=" * 60)
    print("🚀 发票处理全能工具 v1.0")
    print("=" * 60)
    
    args = sys.argv[1:]
    
    if '--help' in args or '-h' in args:
        print("""
使用方法:
    python invoice_toolkit.py              # 全流程（下载+提取+报表）
    python invoice_toolkit.py --extract    # 仅提取和报表
    python invoice_toolkit.py --report     # 仅生成报表（使用现有 PDF）
    python invoice_toolkit.py 260101 260601  # 指定日期范围下载
    python invoice_toolkit.py auto         # 自动日期范围
        """)
        return
    
    # 确定模式
    mode = 'full'
    if '--extract' in args:
        mode = 'extract'
    elif '--report' in args:
        mode = 'report'
    
    # 提取日期参数
    date_args = [a for a in args if not a.startswith('--')]
    date_range = date_args[:2] if len(date_args) >= 2 else None
    
    invoice_dir = None
    
    # 步骤 1: 下载
    if mode == 'full':
        invoice_dir = run_download(date_range if date_range else None)
    
    # 步骤 2: 提取和报表
    if mode in ['full', 'extract', 'report']:
        report_file = run_extract_and_report(invoice_dir)
    
    # 步骤 3: 显示摘要
    show_summary(invoice_dir)
    
    print("\n" + "=" * 60)
    print("✅ 处理完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
