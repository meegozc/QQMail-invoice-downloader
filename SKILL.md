---
name: qq-invoice-downloader
description: QQ邮箱发票自动下载、信息提取、智能分类与统计报表生成工具
version: 1.2.0
author: 83547288@qq.com
category: productivity
tags:
  - invoice
  - email
  - qq-mail
  - automation
  - pdf-extraction
  - report-generation
---

# QQ邮箱发票下载器 Skill

## 📖 功能概述

自动从 QQ 邮箱下载发票邮件，提取发票信息，智能分类并生成多维度统计报表。

### 核心功能

- ✅ **自动下载** - 登录 QQ 邮箱，搜索并下载指定日期范围的发票邮件
- ✅ **多平台支持** - 铁路电子客票、增值税发票、诺诺网、中海油等
- ✅ **信息提取** - 从 PDF 提取发票号码、日期、金额、购买方等关键信息
- ✅ **智能分类** - 按发票类型、金额区间、行业自动分类
- ✅ **去重检测** - 按文件名 + MD5 双重校验，避免重复下载
- ✅ **统计报表** - 生成包含 7 个工作表的 Excel 报表
- ✅ **定时任务** - 支持每月自动执行

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖包
pip install imap-tools pandas openpyxl requests pdfplumber playwright
playwright install chromium
```

### 2. 配置邮箱

编辑 `config.json`：

```json
{
    "qq_email": "你的QQ邮箱@qq.com",
    "qq_password": "你的授权码",
    "invoice_storage_dir": "../invoicefiles"
}
```

或使用交互式配置向导：

```bash
python setup_config.py
```

### 3. 运行下载

```bash
# 一键运行（下载 + 提取 + 报表）
python run_downloader.py

# 指定日期范围
python run_downloader.py 260501 260602

# 仅生成报表
python run_downloader.py --report
```

---

## 📁 文件结构

```
qq-invoice-downloader/
├── config.json                    # 配置文件
├── setup_config.py                # 配置管理工具
├── run_downloader.py              # 一键启动脚本
├── invoice_downloader_v82.py     # 主下载脚本
├── invoice_extractor.py          # 发票信息提取器
├── generate_invoice_report.py    # 报表生成器
├── invoice_toolkit.py            # 全能工具
├── SKILL.md                      # 技能文档（本文件）
└── invoices/                     # 发票存放目录（可选）
```

---

## ⚙️ 配置文件说明

`config.json` 完整配置：

```json
{
    "qq_email": "83547288@qq.com",           // QQ 邮箱地址
    "qq_password": "your_auth_code",         // 邮箱授权码（非 QQ 密码）
    "invoice_storage_dir": "../invoicefiles", // 发票存放目录
    "date_range": {
        "auto": true,                        // 自动计算日期范围
        "default_days": 30                   // 默认搜索天数
    },
    "browser": {
        "headless": true,                    // 浏览器无头模式
        "timeout": 30                        // 超时时间（秒）
    },
    "logging": {
        "level": "INFO",                     // 日志级别
        "save_to_file": true                 // 是否保存到文件
    }
}
```

---

## 📊 报表内容

生成的 Excel 报表包含 7 个工作表：

| 工作表 | 内容 |
|--------|------|
| 发票明细 | 每张发票的详细信息 |
| 分类汇总 | 按发票类型分类统计 |
| 金额区间统计 | 按金额区间分布 |
| 购买方统计 | 按购买方汇总 |
| 时间趋势 | 按月份统计趋势 |
| 去重记录 | 跳过的重复文件记录 |
| 汇总概览 | 总体统计数据 |

---

## 🏷️ 智能分类规则

### 按发票类型

| 类型 | 说明 |
|------|------|
| 交通差旅 | 铁路、航空等交通发票 |
| 增值税发票 | 普通/专用发票 |
| 餐饮服务 | 餐饮类发票 |
| 住宿服务 | 酒店宾馆类发票 |
| 技术服务 | 科技信息类发票 |

### 按金额区间

| 区间 | 范围 |
|------|------|
| 100元以下 | < ¥100 |
| 100-500元 | ¥100 - ¥500 |
| 500-1000元 | ¥500 - ¥1000 |
| 1000-5000元 | ¥1000 - ¥5000 |
| 5000-10000元 | ¥5000 - ¥10000 |
| 10000元以上 | > ¥10000 |

---

## 🔧 常用命令

| 命令 | 功能 |
|------|------|
| `python run_downloader.py` | 全流程（下载+提取+报表） |
| `python run_downloader.py 260101 260601` | 指定日期范围 |
| `python setup_config.py` | 交互式配置向导 |
| `python setup_config.py --show` | 查看当前配置 |
| `python setup_config.py --test` | 测试邮箱连接 |
| `python setup_config.py --reset` | 重置配置 |
| `python invoice_toolkit.py --extract` | 仅提取和报表 |

---

## 🔐 获取 QQ 邮箱授权码

1. 登录 QQ 邮箱网页版
2. 进入 **设置 → 账户**
3. 找到 **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务**
4. 开启 **IMAP/SMTP 服务**
5. 点击 **生成授权码**，按提示发送短信获取

---

## 📂 输出目录

默认结构：

```
invoicefiles/
└── 20260602/                  # 按执行日期创建
    ├── attachments/           # 发票 PDF 文件
    │   ├── 26429165812000204210.pdf
    │   └── 26429365812000003170.pdf
    ├── 发票目录.xlsx          # 下载清单
    ├── 发票统计报表_*.xlsx    # 统计报表
    └── detailed_results.json  # 详细日志
```

---

## 🔄 去重机制

系统会自动检测重复发票：

1. **按文件名检查** - 快速识别同名文件
2. **按 MD5 校验** - 确认内容是否完全相同
3. **智能处理**：
   - ✅ 完全相同 → 跳过，不统计
   - ⚠️ 发票号相同但内容不同（换开/红冲）→ 保留并标记

---

## 🐛 故障排除

| 问题 | 解决方案 |
|------|----------|
| 登录失败 | 检查授权码是否正确（非 QQ 密码） |
| 浏览器无法打开 | 运行 `playwright install chromium` |
| 找不到发票 | 检查日期范围是否包含发票邮件 |
| 提取失败 | 检查 PDF 是否为标准发票格式 |
| 报表打不开 | 确保安装了 openpyxl |

---

## 📋 版本历史

### v1.2.0 (2026-06-02)
- ✅ 按执行日期自动创建子目录
- ✅ 智能去重检测（文件名 + MD5）
- ✅ 发票信息提取（支持铁路、增值税等）
- ✅ 智能分类（按类型、金额、行业）
- ✅ 多维度统计报表
- ✅ 定时任务支持

### v1.0.0 (2026-03-12)
- 初始版本
- QQ 邮箱发票下载
- 多平台支持
- 自动解压

---

## 📞 技术支持

如有问题，请检查：
1. 配置文件格式是否正确（JSON 格式）
2. 邮箱和授权码是否正确
3. 网络连接是否正常
4. 查看日志文件了解详细错误信息
