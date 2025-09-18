#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار سريع لنظام البحث
"""

from legal_search import LegalSearchEngine
import os

def test_search():
    """اختبار سريع للبحث"""
    print("🔍 اختبار نظام البحث القانوني")
    print("=" * 50)
    
    # إنشاء محرك البحث
    engine = LegalSearchEngine()
    
    # عرض الإحصائيات
    stats = engine.get_statistics()
    print(f"📊 الإحصائيات:")
    print(f"   📄 الوثائق: {stats['documents_count']}")
    print(f"   📝 المواد: {stats['articles_count']}")
    
    # اختبارات بحث متنوعة
    test_queries = [
        "العامل",
        "الأجر الأساسي", 
        "صاحب العمل",
        "عقد العمل",
        "التأمين الاجتماعي",
        "الوزارة",
        "الليل",
        "إصابة العمل"
    ]
    
    print(f"\n🔍 نتائج البحث:")
    print("-" * 50)
    
    for query in test_queries:
        results = engine.search(query, limit=2)
        print(f"\n🔎 '{query}': {len(results)} نتيجة")
        
        for i, result in enumerate(results[:1]):  # عرض نتيجة واحدة فقط
            content = result['content'][:80] + "..." if len(result['content']) > 80 else result['content']
            print(f"   📄 المادة ({result['article_number']}) - ص{result['page_number']}")
            print(f"   📝 {content}")
    
    engine.close()
    print(f"\n✅ اكتمل الاختبار!")

if __name__ == "__main__":
    test_search()
