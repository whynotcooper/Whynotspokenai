#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 TOEFL 记录数据格式的脚本
运行方式：python fix_records.py
"""

import os
import sys
import django

# 添加项目到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WhynotEnglish.settings')

# 初始化 Django
django.setup()

from spoken_ai.models import ToeflRecordModel


def fix_record_feedback(record):
    """修复单条记录的 feedback 数据格式"""
    if not record.feedback:
        return False
    
    changed = False
    
    # 修复 recommended_words
    if 'recommended_words' in record.feedback:
        old_words = record.feedback['recommended_words']
        new_words = []
        for item in old_words:
            if isinstance(item, dict):
                new_words.append({
                    'en': item.get('en') or item.get('word') or item.get('english') or '',
                    'zh': item.get('zh') or item.get('chinese') or item.get('meaning') or ''
                })
            else:
                # 如果不是字典，尝试直接使用
                new_words.append({'en': str(item), 'zh': ''})
        
        if new_words != old_words:
            record.feedback['recommended_words'] = new_words
            changed = True
    
    # 修复 recommended_phrases
    if 'recommended_phrases' in record.feedback:
        old_phrases = record.feedback['recommended_phrases']
        new_phrases = []
        for item in old_phrases:
            if isinstance(item, dict):
                new_phrases.append({
                    'en': item.get('en') or item.get('phrase') or item.get('english') or '',
                    'zh': item.get('zh') or item.get('chinese') or item.get('meaning') or ''
                })
            else:
                new_phrases.append({'en': str(item), 'zh': ''})
        
        if new_phrases != old_phrases:
            record.feedback['recommended_phrases'] = new_phrases
            changed = True
    
    # 修复 recommended_sentences
    if 'recommended_sentences' in record.feedback:
        old_sentences = record.feedback['recommended_sentences']
        new_sentences = [
            str(item) if not isinstance(item, str) else item
            for item in old_sentences
        ]
        if new_sentences != old_sentences:
            record.feedback['recommended_sentences'] = new_sentences
            changed = True
    
    return changed


def fix_record_score_details(record):
    """修复 score_details 数据格式"""
    if not record.score_details or not isinstance(record.score_details, dict):
        # 创建默认结构
        record.score_details = {
            'delivery': {'score': None, 'problems': [], 'evidence': [], 'fixes': []},
            'language_use': {'score': None, 'problems': [], 'evidence': [], 'fixes': []},
            'topic_development': {'score': None, 'problems': [], 'evidence': [], 'fixes': []}
        }
        return True
    
    changed = False
    for dim in ['delivery', 'language_use', 'topic_development']:
        if dim in record.score_details:
            dim_data = record.score_details[dim]
            if isinstance(dim_data, dict):
                # 确保所有字段存在
                if 'score' not in dim_data:
                    dim_data['score'] = None
                    changed = True
                if 'problems' not in dim_data:
                    dim_data['problems'] = []
                    changed = True
                if 'evidence' not in dim_data:
                    dim_data['evidence'] = []
                    changed = True
                if 'fixes' not in dim_data:
                    dim_data['fixes'] = []
                    changed = True
        else:
            record.score_details[dim] = {
                'score': None,
                'problems': [],
                'evidence': [],
                'fixes': []
            }
            changed = True
    
    return changed


def main():
    """主函数"""
    print("🔧 开始修复 TOEFL 记录数据格式...")
    print()
    
    # 获取所有记录
    records = ToeflRecordModel.objects.all()
    total = records.count()
    print(f"📊 总共有 {total} 条记录")
    print()
    
    fixed_count = 0
    error_count = 0
    
    for record in records:
        try:
            feedback_changed = fix_record_feedback(record)
            score_changed = fix_record_score_details(record)
            
            if feedback_changed or score_changed:
                record.save()
                fixed_count += 1
                print(f"✅ 修复记录 ID {record.id}")
        
        except Exception as e:
            error_count += 1
            print(f"❌ 修复记录 ID {record.id} 失败: {e}")
    
    print()
    print("=" * 50)
    print(f"📈 修复完成！")
    print(f"   - 修复记录数: {fixed_count}")
    print(f"   - 失败记录数: {error_count}")
    print("=" * 50)


if __name__ == '__main__':
    main()
