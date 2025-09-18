#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
واجهة بحث تفاعلية لنظام فهرسة القوانين البحرينية
"""

from legal_search import LegalSearchEngine
import os
import sys

def print_header():
    """طباعة رأس البرنامج"""
    print("=" * 60)
    print("🔍 نظام البحث في القوانين البحرينية")
    print("=" * 60)
    print("📋 الأوامر المتاحة:")
    print("   🔎 للبحث: اكتب كلمة أو عبارة")
    print("   📊 للإحصائيات: اكتب 'stats'")
    print("   🚪 للخروج: اكتب 'exit' أو 'quit'")
    print("   ❓ للمساعدة: اكتب 'help'")
    print("-" * 60)

def format_search_result(result, index):
    """تنسيق نتيجة البحث للعرض"""
    print(f"\n📄 النتيجة {index + 1}:")
    print(f"   📑 الوثيقة: {result['document_name']}")
    print(f"   📄 الصفحة: {result['page_number']}")
    
    if result['chapter']:
        print(f"   📚 الباب: {result['chapter']}")
    
    if result['section']:
        print(f"   📖 الفصل: {result['section']}")
    
    if result['article_number']:
        print(f"   📝 المادة: ({result['article_number']})")
    
    if result['title']:
        print(f"   🏷️  العنوان: {result['title']}")
    
    print(f"   📋 النوع: {get_article_type_name(result['article_type'])}")
    
    # عرض المحتوى مع تحديد الطول
    content = result['content']
    if len(content) > 200:
        content = content[:200] + "..."
    
    print(f"   📝 المحتوى:")
    print(f"      {content}")

def get_article_type_name(article_type):
    """ترجمة نوع المادة إلى العربية"""
    type_names = {
        'article': 'مادة قانونية',
        'definition': 'تعريف',
        'general': 'نص عام'
    }
    return type_names.get(article_type, article_type)

def show_statistics(engine):
    """عرض إحصائيات قاعدة البيانات"""
    stats = engine.get_statistics()
    
    print("\n📊 إحصائيات قاعدة البيانات:")
    print("-" * 40)
    print(f"📄 عدد الوثائق المفهرسة: {stats['documents_count']}")
    print(f"📝 إجمالي المواد والنصوص: {stats['articles_count']}")
    
    if 'articles_by_type' in stats:
        print(f"\n📋 تفصيل المحتوى:")
        for article_type, count in stats['articles_by_type'].items():
            type_name = get_article_type_name(article_type)
            print(f"   • {type_name}: {count}")

def show_help():
    """عرض المساعدة"""
    print("\n❓ المساعدة:")
    print("-" * 40)
    print("🔍 كيفية البحث:")
    print("   • اكتب كلمة أو عبارة للبحث عنها")
    print("   • مثال: 'العامل' أو 'حقوق العمال'")
    print("   • يمكنك البحث بكلمات متعددة")
    
    print("\n📊 أوامر خاصة:")
    print("   • 'stats' - عرض إحصائيات قاعدة البيانات")
    print("   • 'help' - عرض هذه المساعدة")
    print("   • 'exit' أو 'quit' - الخروج من البرنامج")
    
    print("\n💡 نصائح:")
    print("   • استخدم كلمات مفتاحية واضحة")
    print("   • جرب كلمات مختلفة إذا لم تجد النتائج المطلوبة")
    print("   • النظام يبحث في جميع أجزاء النص")

def main():
    """الدالة الرئيسية للواجهة التفاعلية"""
    # التحقق من وجود قاعدة البيانات
    if not os.path.exists("legal_database.db"):
        print("❌ لم يتم العثور على قاعدة البيانات!")
        print("💡 يرجى تشغيل 'python legal_search.py' أولاً لإنشاء الفهرس")
        return
    
    # إنشاء محرك البحث
    try:
        engine = LegalSearchEngine()
        print_header()
        
        # التحقق من وجود بيانات
        stats = engine.get_statistics()
        if stats['documents_count'] == 0:
            print("⚠️  قاعدة البيانات فارغة!")
            print("💡 يرجى تشغيل 'python legal_search.py' أولاً لفهرسة الوثائق")
            return
        
        print(f"✅ تم تحميل {stats['documents_count']} وثيقة تحتوي على {stats['articles_count']} عنصر")
        
        # حلقة التفاعل الرئيسية
        while True:
            try:
                # قراءة الاستعلام من المستخدم
                query = input("\n🔍 ادخل استعلامك: ").strip()
                
                if not query:
                    continue
                
                # معالجة الأوامر الخاصة
                if query.lower() in ['exit', 'quit', 'خروج']:
                    print("👋 شكراً لاستخدام نظام البحث!")
                    break
                
                elif query.lower() in ['stats', 'إحصائيات']:
                    show_statistics(engine)
                    continue
                
                elif query.lower() in ['help', 'مساعدة']:
                    show_help()
                    continue
                
                # تنفيذ البحث
                print(f"\n🔎 البحث عن: '{query}'...")
                results = engine.search(query, limit=10)
                
                if not results:
                    print("❌ لم يتم العثور على نتائج مطابقة")
                    print("💡 جرب:")
                    print("   • كلمات مختلفة أو مرادفات")
                    print("   • كلمات أقل تحديداً")
                    print("   • التحقق من الإملاء")
                else:
                    print(f"✅ تم العثور على {len(results)} نتيجة:")
                    
                    # عرض النتائج
                    for i, result in enumerate(results):
                        format_search_result(result, i)
                        
                        # توقف بعد كل 3 نتائج للسؤال عن المتابعة
                        if (i + 1) % 3 == 0 and i + 1 < len(results):
                            continue_search = input(f"\n📄 عرض المزيد من النتائج؟ (y/n): ").strip().lower()
                            if continue_search not in ['y', 'yes', 'نعم', 'ن']:
                                break
            
            except KeyboardInterrupt:
                print("\n\n👋 تم إيقاف البرنامج بواسطة المستخدم")
                break
            except Exception as e:
                print(f"\n❌ حدث خطأ: {e}")
                print("💡 يرجى المحاولة مرة أخرى")
    
    except Exception as e:
        print(f"❌ فشل في تهيئة محرك البحث: {e}")
    finally:
        if 'engine' in locals():
            engine.close()

if __name__ == "__main__":
    main()
