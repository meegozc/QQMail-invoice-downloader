#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票统计报表生成器 - 生成分类汇总的 Excel 报表
================================================
功能：
1. 批量提取 PDF 发票信息
2. 生成详细发票清单
3. 按分类生成统计汇总表
4. 生成可视化图表（可选）
"""

import os
import json
import glob
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

import pandas as pd
from invoice_extractor import InvoiceExtractor, extract_invoice


class InvoiceReportGenerator:
    """发票统计报表生成器"""
    
    def __init__(self, invoice_dir: str, output_dir: str = None):
        self.invoice_dir = Path(invoice_dir)
        self.output_dir = Path(output_dir) if output_dir else self.invoice_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.invoice_data = []
        self.duplicate_info = []  # 记录去重信息
        
    def scan_invoices(self) -> list:
        """扫描目录下的所有 PDF 发票"""
        pdf_files = list(self.invoice_dir.glob('**/*.pdf'))
        print(f"🔍 找到 {len(pdf_files)} 个 PDF 文件")
        return [str(p) for p in pdf_files]
    
    def deduplicate_invoices(self, pdf_files: list) -> list:
        """发票去重：按发票号码+MD5 校验"""
        if not pdf_files:
            return []
        
        import hashlib
        
        seen_invoices = {}  # {invoice_number: {md5, file_path, data}}
        duplicates = []
        unique_files = []
        
        for pdf_path in pdf_files:
            # 计算文件 MD5
            with open(pdf_path, 'rb') as f:
                file_md5 = hashlib.md5(f.read()).hexdigest()
            
            # 快速提取发票号码（不解析完整内容）
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    text = pdf.pages[0].extract_text() or ""
            except:
                text = ""
            
            # 提取发票号码
            import re
            match = re.search(r'发票号码[::\s]*([0-9]+)', text)
            invoice_num = match.group(1) if match else None
            
            if not invoice_num:
                # 无法识别发票号码，保留文件
                unique_files.append(pdf_path)
                continue
            
            if invoice_num in seen_invoices:
                # 发现重复发票
                existing = seen_invoices[invoice_num]
                
                if existing['md5'] == file_md5:
                    # MD5 相同，完全重复，跳过
                    duplicates.append({
                        'file': pdf_path,
                        'reason': '完全重复（MD5 相同）',
                        'duplicate_of': existing['file_path']
                    })
                else:
                    # MD5 不同，可能是同一发票的不同版本/换开
                    duplicates.append({
                        'file': pdf_path,
                        'reason': '发票号相同但内容不同（可能是换开/红冲）',
                        'duplicate_of': existing['file_path']
                    })
                    # 仍然保留这个文件，因为内容不同
                    unique_files.append(pdf_path)
            else:
                # 新发票
                seen_invoices[invoice_num] = {
                    'md5': file_md5,
                    'file_path': pdf_path,
                }
                unique_files.append(pdf_path)
        
        # 打印去重结果
        if duplicates:
            print(f"\n🔄 发票去重结果:")
            print(f"   原始文件: {len(pdf_files)} 个")
            print(f"   唯一发票: {len(unique_files)} 张")
            print(f"   跳过重复: {len(duplicates)} 个")
            print()
            for dup in duplicates:
                from pathlib import Path
                print(f"   ⏭️  跳过: {Path(dup['file']).name}")
                print(f"       原因: {dup['reason']}")
                print(f"       保留: {Path(dup['duplicate_of']).name}")
                print()
        
        # 保存去重信息供报表使用
        self.duplicate_info = duplicates
        
        return unique_files
    
    def extract_all(self, pdf_files: list = None):
        """批量提取发票信息"""
        if pdf_files is None:
            pdf_files = self.scan_invoices()
            # 自动去重
            pdf_files = self.deduplicate_invoices(pdf_files)
        
        print(f"\n📄 开始提取 {len(pdf_files)} 张发票信息...\n")
        
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"  [{i}/{len(pdf_files)}] 提取: {Path(pdf_path).name}")
            result = extract_invoice(pdf_path)
            self.invoice_data.append(result)
        
        # 显示统计
        success = sum(1 for d in self.invoice_data if d['status'] == 'success')
        failed = sum(1 for d in self.invoice_data if d['status'] == 'error')
        print(f"\n✅ 提取完成: 成功 {success} 张, 失败 {failed} 张")
        
        return self.invoice_data
    
    def generate_excel_report(self) -> str:
        """生成 Excel 报表"""
        if not self.invoice_data:
            print("❌ 没有发票数据，请先调用 extract_all()")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f"发票统计报表_{timestamp}.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 1. 发票明细表
            self._write_detail_sheet(writer)
            
            # 2. 分类汇总表
            self._write_category_summary(writer)
            
            # 3. 金额区间统计
            self._write_amount_stats(writer)
            
            # 4. 购买方统计
            self._write_buyer_stats(writer)
            
            # 5. 时间趋势（按月份）
            self._write_time_trend(writer)
            
            # 6. 去重记录
            self._write_duplicate_records(writer)
            
            # 7. 汇总统计
            self._write_overview(writer)
        
        print(f"\n📊 报表已生成: {output_file}")
        return str(output_file)
    
    def _write_detail_sheet(self, writer):
        """发票明细表"""
        rows = []
        for inv in self.invoice_data:
            if inv['status'] != 'success':
                continue
            
            row = {
                '序号': len(rows) + 1,
                '文件名': inv.get('file_name', ''),
                '发票类型': inv.get('invoice_type', ''),
                '发票号码': inv.get('invoice_number', ''),
                '开票日期': inv.get('invoice_date', ''),
                '购买方': inv.get('buyer_name', ''),
                '购买方税号': inv.get('buyer_tax_id', ''),
                '销售方': inv.get('seller_name', ''),
                '金额': inv.get('total_amount', 0),
                '分类-大类': inv.get('classification', {}).get('category', ''),
                '分类-小类': inv.get('classification', {}).get('subcategory', ''),
                '金额区间': inv.get('classification', {}).get('amount_level', ''),
                '行业': inv.get('classification', {}).get('industry', ''),
                '标签': ', '.join(inv.get('classification', {}).get('tags', [])),
            }
            
            # 铁路特有字段
            if inv.get('invoice_type') == 'railway':
                row['出发站'] = inv.get('departure', '')
                row['到达站'] = inv.get('arrival', '')
                row['车次'] = inv.get('train_number', '')
                row['乘车日期'] = inv.get('travel_date', '')
                row['座位'] = inv.get('seat', '')
                row['乘车人'] = inv.get('passenger', '')
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name='发票明细', index=False)
    
    def _write_category_summary(self, writer):
        """分类汇总表"""
        # 按大类统计
        category_stats = defaultdict(lambda: {'count': 0, 'total_amount': 0})
        
        for inv in self.invoice_data:
            if inv['status'] != 'success':
                continue
            
            cat = inv.get('classification', {}).get('category', '未分类')
            amount = inv.get('total_amount', 0)
            
            category_stats[cat]['count'] += 1
            category_stats[cat]['total_amount'] += amount
        
        rows = []
        for cat, stats in sorted(category_stats.items(), key=lambda x: x[1]['total_amount'], reverse=True):
            rows.append({
                '分类': cat,
                '发票数量': stats['count'],
                '总金额': stats['total_amount'],
                '占比': f"{stats['count']/len(self.invoice_data)*100:.1f}%" if self.invoice_data else '0%',
            })
        
        # 合计行
        total_count = sum(r['发票数量'] for r in rows)
        total_amount = sum(r['总金额'] for r in rows)
        rows.append({
            '分类': '合计',
            '发票数量': total_count,
            '总金额': total_amount,
            '占比': '100%',
        })
        
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name='分类汇总', index=False)
    
    def _write_amount_stats(self, writer):
        """金额区间统计"""
        amount_levels = defaultdict(lambda: {'count': 0, 'total_amount': 0})
        
        for inv in self.invoice_data:
            if inv['status'] != 'success':
                continue
            
            level = inv.get('classification', {}).get('amount_level', '未知')
            amount = inv.get('total_amount', 0)
            
            amount_levels[level]['count'] += 1
            amount_levels[level]['total_amount'] += amount
        
        rows = []
        for level in ['100元以下', '100-500元', '500-1000元', '1000-5000元', '5000-10000元', '10000元以上', '未知']:
            if level in amount_levels:
                stats = amount_levels[level]
                rows.append({
                    '金额区间': level,
                    '发票数量': stats['count'],
                    '总金额': stats['total_amount'],
                })
        
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name='金额区间统计', index=False)
    
    def _write_buyer_stats(self, writer):
        """购买方统计"""
        buyer_stats = defaultdict(lambda: {'count': 0, 'total_amount': 0})
        
        for inv in self.invoice_data:
            if inv['status'] != 'success':
                continue
            
            buyer = inv.get('buyer_name', '未知')
            amount = inv.get('total_amount', 0)
            
            buyer_stats[buyer]['count'] += 1
            buyer_stats[buyer]['total_amount'] += amount
        
        rows = []
        for buyer, stats in sorted(buyer_stats.items(), key=lambda x: x[1]['total_amount'], reverse=True):
            rows.append({
                '购买方': buyer,
                '发票数量': stats['count'],
                '总金额': stats['total_amount'],
                '税号': next((inv.get('buyer_tax_id', '') for inv in self.invoice_data 
                             if inv.get('buyer_name') == buyer and inv['status'] == 'success'), ''),
            })
        
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name='购买方统计', index=False)
    
    def _write_time_trend(self, writer):
        """时间趋势统计"""
        monthly_stats = defaultdict(lambda: {'count': 0, 'total_amount': 0})
        
        for inv in self.invoice_data:
            if inv['status'] != 'success':
                continue
            
            date_str = inv.get('invoice_date', '') or inv.get('travel_date', '')
            if not date_str:
                continue
            
            # 提取年月
            match = None
            for pattern in [r'(\d{4}年\d{2}月)', r'(\d{4}-\d{2})']:
                import re
                match = re.search(pattern, date_str)
                if match:
                    break
            
            if match:
                month = match.group(1)
                amount = inv.get('total_amount', 0)
                monthly_stats[month]['count'] += 1
                monthly_stats[month]['total_amount'] += amount
        
        rows = []
        for month in sorted(monthly_stats.keys()):
            stats = monthly_stats[month]
            rows.append({
                '月份': month,
                '发票数量': stats['count'],
                '总金额': stats['total_amount'],
            })
        
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name='时间趋势', index=False)
    
    def _write_duplicate_records(self, writer):
        """去重记录表"""
        if not self.duplicate_info:
            # 没有重复记录，写入空表说明
            rows = [{'状态': '无重复发票', '说明': '所有发票均为唯一'}]
            df = pd.DataFrame(rows)
            df.to_excel(writer, sheet_name='去重记录', index=False)
            return
        
        rows = []
        for i, dup in enumerate(self.duplicate_info, 1):
            from pathlib import Path
            rows.append({
                '序号': i,
                '跳过的文件': Path(dup['file']).name,
                '跳过的路径': str(Path(dup['file']).parent),
                '保留的文件': Path(dup['duplicate_of']).name,
                '保留的路径': str(Path(dup['duplicate_of']).parent),
                '去重原因': dup['reason'],
                '处理结果': '已跳过，未重复统计'
            })
        
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name='去重记录', index=False)
    
    def _write_overview(self, writer):
        """汇总统计概览"""
        total_files = len(self.invoice_data) + len(self.duplicate_info)
        success = sum(1 for d in self.invoice_data if d['status'] == 'success')
        failed = sum(1 for d in self.invoice_data if d['status'] == 'error')
        duplicates = len(self.duplicate_info)
        total_amount = sum(d.get('total_amount', 0) for d in self.invoice_data if d['status'] == 'success')
        
        rows = [
            {'项目': '扫描文件总数', '数值': total_files},
            {'项目': '唯一发票数', '数值': success + failed},
            {'项目': '跳过重复', '数值': duplicates},
            {'项目': '成功提取', '数值': success},
            {'项目': '提取失败', '数值': failed},
            {'项目': '总金额', '数值': f"¥{total_amount:.2f}"},
            {'项目': '平均金额', '数值': f"¥{total_amount/success:.2f}" if success > 0 else '¥0.00'},
            {'项目': '生成时间', '数值': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
        ]
        
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name='汇总概览', index=False)


def generate_report(invoice_dir: str, output_dir: str = None) -> str:
    """便捷函数：生成发票统计报表"""
    generator = InvoiceReportGenerator(invoice_dir, output_dir)
    generator.extract_all()
    return generator.generate_excel_report()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        invoice_dir = sys.argv[1]
    else:
        invoice_dir = "invoices"
    
    output_dir = invoice_dir
    
    print("=" * 60)
    print("📊 发票统计报表生成器")
    print("=" * 60)
    
    result_file = generate_report(invoice_dir, output_dir)
    
    if result_file:
        print(f"\n✅ 报表生成成功!")
        print(f"📁 保存位置: {result_file}")
