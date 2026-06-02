#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票信息提取器 - 从 PDF 发票中提取关键信息
=============================================
支持发票类型：
- 增值税普通发票/专用发票
- 铁路电子客票
- 航空运输电子客票
- 通用机打发票
"""

import pdfplumber
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class InvoiceExtractor:
    """发票信息提取器"""
    
    # 发票类型识别
    INVOICE_TYPES = {
        'railway': ['铁路', '电子客票', '12306', '客票'],
        'vat_normal': ['增值税普通发票', '电子普通发票'],
        'vat_special': ['增值税专用发票', '电子专用发票'],
        'flight': ['航空运输', '机票', '航班'],
        'general': ['通用机打发票', '定额发票'],
    }
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        self.raw_data = {}
        
    def extract(self) -> Dict:
        """提取发票信息"""
        result = {
            'file_path': self.pdf_path,
            'file_name': Path(self.pdf_path).name,
            'extract_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'invoice_type': 'unknown',
            'invoice_code': '',
            'invoice_number': '',
            'invoice_date': '',
            'check_code': '',
            'buyer_name': '',
            'buyer_tax_id': '',
            'seller_name': '',
            'seller_tax_id': '',
            'amount': 0.0,
            'tax_amount': 0.0,
            'total_amount': 0.0,
            'amount_cn': '',  # 大写金额
            'items': [],  # 货物/服务明细
            'remarks': '',
            'raw_text': '',
            'classification': {},  # 分类信息
            'status': 'success',
            'error': '',
        }
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                if not pdf.pages:
                    result['status'] = 'error'
                    result['error'] = 'PDF 无页面'
                    return result
                
                # 提取所有文本
                all_text = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text.append(text)
                
                self.text = '\n'.join(all_text)
                result['raw_text'] = self.text
                
                # 识别发票类型
                result['invoice_type'] = self._detect_invoice_type()
                
                # 根据类型提取信息
                if result['invoice_type'] == 'railway':
                    self._extract_railway(result)
                elif result['invoice_type'] in ['vat_normal', 'vat_special']:
                    self._extract_vat(result)
                else:
                    self._extract_generic(result)
                
                # 自动分类
                result['classification'] = self._classify(result)
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def _detect_invoice_type(self) -> str:
        """检测发票类型"""
        text_lower = self.text.lower()
        
        for inv_type, keywords in self.INVOICE_TYPES.items():
            if any(kw in self.text or kw.lower() in text_lower for kw in keywords):
                return inv_type
        
        return 'unknown'
    
    def _extract_railway(self, result: Dict):
        """提取铁路电子客票信息"""
        text = self.text
        
        # 发票号码
        match = re.search(r'发票号码[::\s]*([0-9]+)', text)
        if match:
            result['invoice_number'] = match.group(1)
            result['invoice_code'] = match.group(1)[:12] if len(match.group(1)) > 12 else match.group(1)
        
        # 开票日期
        match = re.search(r'开票日期[::\s]*(\d{4}年\d{2}月\d{2}日)', text)
        if match:
            result['invoice_date'] = match.group(1)
        
        # 出发站和到达站
        match = re.search(r'([^\s]+)\s+G?\d+\s+([^\s]+)', text)
        if match:
            result['departure'] = match.group(1).replace('站', '')
            result['arrival'] = match.group(2).replace('站', '')
        
        # 车次
        match = re.search(r'((?:G|D|C|Z|T|K)\d{3,4})', text)
        if match:
            result['train_number'] = match.group(1)
        
        # 乘车日期时间
        match = re.search(r'(\d{4}年\d{2}月\d{2}日\s+\d{2}:\d{2}开)', text)
        if match:
            result['travel_date'] = match.group(1).replace('开', '')
        
        # 座位信息
        match = re.search(r'(\d+车\d+[A-Z]\d*号\s+[^￥\n]+?座)', text)
        if match:
            result['seat'] = match.group(1).strip()
        
        # 乘车人（身份证号后面的名字）
        match = re.search(r'\d{17}[*Xx]\d\s+([^\s\n]{2,4})', text)
        if match:
            name = match.group(1)
            if not any(kw in name for kw in ['税务局', '铁路', '客票']):
                result['passenger'] = name
        
        # 备用：如果没找到乘车人，尝试其他模式
        if not result.get('passenger'):
            match = re.search(r'军\s*([^\s\n]{2,4})', text)
            if match:
                result['passenger'] = match.group(1).strip()
        
        # 票价
        match = re.search(r'[￥¥]\s*([\d.]+)', text)
        if match:
            result['total_amount'] = float(match.group(1))
            result['amount'] = result['total_amount']
        
        # 购买方
        match = re.search(r'购买方名称[::\s]*([^\n]+)', text)
        if match:
            result['buyer_name'] = match.group(1).strip()
        
        # 税号
        match = re.search(r'统一社会信用代码[::\s]*([A-Z0-9]+)', text)
        if match:
            result['buyer_tax_id'] = match.group(1)
    
    def _extract_vat(self, result: Dict):
        """提取增值税发票信息"""
        text = self.text
        
        # 发票代码
        match = re.search(r'发票代码[::\s]*([0-9]+)', text)
        if match:
            result['invoice_code'] = match.group(1)
        
        # 发票号码
        match = re.search(r'发票号码[::\s]*([0-9]+)', text)
        if match:
            result['invoice_number'] = match.group(1)
        
        # 开票日期
        match = re.search(r'开票日期[::\s]*(\d{4}年\d{2}月\d{2}日)', text)
        if match:
            result['invoice_date'] = match.group(1)
        
        # 校验码
        match = re.search(r'校验码[::\s]*([0-9]+)', text)
        if match:
            result['check_code'] = match.group(1)
        
        # 购买方名称
        match = re.search(r'购买方.*?名称[::\s]*([^\n]+)', text)
        if match:
            result['buyer_name'] = match.group(1).strip()
        
        # 购买方税号
        match = re.search(r'购买方.*?纳税人识别号[::\s]*([A-Z0-9]+)', text)
        if match:
            result['buyer_tax_id'] = match.group(1)
        
        # 销售方名称
        match = re.search(r'销售方.*?名称[::\s]*([^\n]+)', text)
        if match:
            result['seller_name'] = match.group(1).strip()
        
        # 销售方税号
        match = re.search(r'销售方.*?纳税人识别号[::\s]*([A-Z0-9]+)', text)
        if match:
            result['seller_tax_id'] = match.group(1)
        
        # 金额
        match = re.search(r'[小写¥￥]\s*([\d.]+)', text)
        if match:
            result['total_amount'] = float(match.group(1))
        
        # 价税合计
        match = re.search(r'价税合计.*?[\(（]小写[\)）]\s*[\(（]￥([^\)）]+)', text)
        if match:
            try:
                result['total_amount'] = float(match.group(1))
            except:
                pass
        
        # 税额
        match = re.search(r'税额[::\s]*([\d.]+)', text)
        if match:
            result['tax_amount'] = float(match.group(1))
        
        # 货物明细（简化版）
        lines = text.split('\n')
        items = []
        for line in lines:
            if any(kw in line for kw in ['货物', '服务', '名称', '规格']):
                if not any(kw in line for kw in ['购买方', '销售方', '密码']):
                    items.append(line.strip())
        result['items'] = items[:5]  # 最多取5条
    
    def _extract_generic(self, result: Dict):
        """通用提取逻辑"""
        # 尝试提取所有可能的信息
        self._extract_vat(result)  # 复用增值税提取逻辑
        
        # 如果没有找到金额，尝试其他模式
        if result['total_amount'] == 0:
            match = re.search(r'[￥¥]\s*([\d.]+)', self.text)
            if match:
                result['total_amount'] = float(match.group(1))
    
    def _classify(self, result: Dict) -> Dict:
        """智能分类"""
        classification = {
            'category': '',  # 大类
            'subcategory': '',  # 小类
            'amount_level': '',  # 金额区间
            'industry': '',  # 行业（根据销售方判断）
            'tags': [],  # 标签
        }
        
        # 按发票类型分类
        if result['invoice_type'] == 'railway':
            classification['category'] = '交通差旅'
            classification['subcategory'] = '铁路'
            classification['tags'].append('高铁' if 'G' in result.get('train_number', '') else '火车')
            
        elif result['invoice_type'] in ['vat_normal', 'vat_special']:
            classification['category'] = '增值税发票'
            classification['subcategory'] = '专用发票' if result['invoice_type'] == 'vat_special' else '普通发票'
            
            # 根据销售方判断行业
            seller = result.get('seller_name', '')
            industry_map = {
                '餐饮': '餐饮服务',
                '酒店': '住宿服务',
                '宾馆': '住宿服务',
                '科技': '技术服务',
                '信息': '技术服务',
                '咨询': '咨询服务',
                '广告': '广告服务',
                '物流': '物流服务',
                '快递': '物流服务',
                '贸易': '商品贸易',
                '商贸': '商品贸易',
            }
            for kw, industry in industry_map.items():
                if kw in seller:
                    classification['industry'] = industry
                    break
            
        # 金额区间分类
        amount = result.get('total_amount', 0)
        if amount < 100:
            classification['amount_level'] = '100元以下'
        elif amount < 500:
            classification['amount_level'] = '100-500元'
        elif amount < 1000:
            classification['amount_level'] = '500-1000元'
        elif amount < 5000:
            classification['amount_level'] = '1000-5000元'
        elif amount < 10000:
            classification['amount_level'] = '5000-10000元'
        else:
            classification['amount_level'] = '10000元以上'
        
        # 添加标签
        if result.get('buyer_name'):
            classification['tags'].append(result['buyer_name'][:10])
        
        return classification


def extract_invoice(pdf_path: str) -> Dict:
    """便捷函数：提取单张发票信息"""
    extractor = InvoiceExtractor(pdf_path)
    return extractor.extract()


def extract_multiple(pdf_paths: list) -> list:
    """便捷函数：批量提取发票信息"""
    results = []
    for path in pdf_paths:
        result = extract_invoice(path)
        results.append(result)
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
    else:
        pdf_file = "invoices/26429165812000204210.pdf"
    
    print(f"📄 正在提取: {pdf_file}\n")
    
    result = extract_invoice(pdf_file)
    
    print("=" * 60)
    print("📊 发票信息提取结果")
    print("=" * 60)
    
    if result['status'] == 'success':
        print(f"发票类型: {result['invoice_type']}")
        print(f"发票号码: {result['invoice_number']}")
        print(f"开票日期: {result['invoice_date']}")
        print(f"购买方: {result['buyer_name']}")
        print(f"金额: ¥{result['total_amount']:.2f}")
        
        print(f"\n📋 分类信息:")
        for k, v in result['classification'].items():
            if v:
                print(f"  {k}: {v}")
    else:
        print(f"❌ 提取失败: {result['error']}")
