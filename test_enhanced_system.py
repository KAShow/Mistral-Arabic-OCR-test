"""
اختبار شامل للنظام المحسن
يختبر جميع المكونات الجديدة والتحسينات
"""

import os
import sys
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

def test_enhanced_components():
    """اختبار المكونات المحسنة"""
    print("🔍 اختبار المكونات المحسنة...")
    
    tests_passed = 0
    tests_total = 0
    
    # اختبار محسن تنظيف النصوص
    print("\n📋 اختبار محسن تنظيف النصوص...")
    tests_total += 1
    try:
        from content_cleaner import content_cleaner
        
        test_text = """
        ![img-0.jpeg](img-0.jpeg)
        
        # قانون العمل في القطاع الأهلي
        
        $$
        \\begin{aligned}
        & \\text{هذا نص تجريبي}
        \\end{aligned}
        $$
        
        هذا نص عربي عادي يجب أن يبقى.
        """
        
        result = content_cleaner.clean_content(test_text)
        
        if result['is_useful'] and 'تم إزالة مراجع الصور' in result['improvements']:
            print("   ✅ تنظيف النصوص يعمل بشكل صحيح")
            tests_passed += 1
        else:
            print("   ❌ مشكلة في تنظيف النصوص")
            
    except Exception as e:
        print(f"   ❌ خطأ في محسن تنظيف النصوص: {e}")
    
    # اختبار مستخرج العناوين
    print("\n📝 اختبار مستخرج العناوين...")
    tests_total += 1
    try:
        from title_extractor import title_extractor
        
        test_pages = [
            "![img-0.jpeg](img-0.jpeg)\n\n# قانون العمل",
            "قانون رقم (36) لسنة 2012\nبإصدار قانون العمل في القطاع الأهلي"
        ]
        
        result = title_extractor.extract_title_from_pages(test_pages)
        
        if result['title'] and 'قانون' in result['title']:
            print("   ✅ استخراج العناوين يعمل بشكل صحيح")
            print(f"      العنوان المستخرج: {result['full_title']}")
            tests_passed += 1
        else:
            print("   ❌ مشكلة في استخراج العناوين")
            
    except Exception as e:
        print(f"   ❌ خطأ في مستخرج العناوين: {e}")
    
    # اختبار الفهرسة القانونية
    print("\n📚 اختبار الفهرسة القانونية...")
    tests_total += 1
    try:
        from legal_indexer import legal_indexer
        
        test_legal_text = """
        الباب الأول
        تعاريف وأحكام عامة
        
        الفصل الأول
        تعاريف
        
        المادة (1)
        في تطبيق أحكام هذا القانون، يكون للكلمات والعبارات التالية المعاني المبينة قرين كل منها.
        
        المادة (2)
        يسري هذا القانون على جميع العمال وأصحاب الأعمال في القطاع الأهلي.
        """
        
        result = legal_indexer.create_comprehensive_index(test_legal_text)
        
        structure = result['legal_structure']
        has_articles = 'مادة' in structure and len(structure['مادة']) > 0
        has_keywords = len(result['keywords']) > 0
        
        if has_articles and has_keywords:
            print("   ✅ الفهرسة القانونية تعمل بشكل صحيح")
            print(f"      المواد المكتشفة: {len(structure.get('مادة', []))}")
            print(f"      الكلمات المفتاحية: {len(result['keywords'])}")
            tests_passed += 1
        else:
            print("   ❌ مشكلة في الفهرسة القانونية")
            
    except Exception as e:
        print(f"   ❌ خطأ في الفهرسة القانونية: {e}")
    
    # اختبار المعالج المتقدم
    print("\n🚀 اختبار المعالج المتقدم...")
    tests_total += 1
    try:
        from advanced_text_processor import advanced_processor
        
        test_pages = [
            "![img-0.jpeg](img-0.jpeg)\n\n# قانون العمل",
            """قانون رقم (36) لسنة 2012
            بإصدار قانون العمل في القطاع الأهلي
            
            المادة (1)
            يسري هذا القانون على جميع العمال."""
        ]
        
        result = advanced_processor.process_document_pages(test_pages, "test.pdf")
        
        has_title = result['title'].get('title') is not None
        has_content = len(result['content']['full_text']) > 0
        has_quality = result['quality']['overall_score'] > 0
        
        if has_title and has_content and has_quality:
            print("   ✅ المعالج المتقدم يعمل بشكل صحيح")
            print(f"      العنوان: {result['title'].get('full_title', 'غير محدد')}")
            print(f"      درجة الجودة: {result['quality']['overall_score']:.2f}")
            tests_passed += 1
        else:
            print("   ❌ مشكلة في المعالج المتقدم")
            
    except Exception as e:
        print(f"   ❌ خطأ في المعالج المتقدم: {e}")
    
    return tests_passed, tests_total

def test_database_enhancements():
    """اختبار تحسينات قاعدة البيانات"""
    print("\n💾 اختبار تحسينات قاعدة البيانات...")
    
    try:
        from supabase_client import db_manager
        
        if not db_manager:
            print("   ❌ عميل قاعدة البيانات غير متاح")
            return False
        
        # اختبار الاتصال الأساسي
        docs = db_manager.get_all_documents()
        print(f"   ✅ تم جلب {len(docs)} وثيقة من قاعدة البيانات")
        
        # اختبار البحث
        if docs:
            search_results = db_manager.search_documents("قانون")
            print(f"   ✅ البحث يعمل - وجد {len(search_results)} نتيجة")
        
        print("   ℹ️  للتأكد من التحسينات الجديدة، شغل السكربت enhanced_database_schema.sql")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ في قاعدة البيانات: {e}")
        return False

def test_integration():
    """اختبار التكامل بين المكونات"""
    print("\n🔗 اختبار التكامل بين المكونات...")
    
    try:
        # محاكاة معالجة وثيقة كاملة
        from advanced_text_processor import advanced_processor
        
        sample_pages = [
            """![img-0.jpeg](img-0.jpeg)
            
            # قانون العمل في القطاع الأهلي
            
            ![img-1.jpeg](img-1.jpeg)""",
            
            """قانون رقم (36) لسنة 2012
            بإصدار قانون العمل في القطاع الأهلي
            
            $$\\begin{aligned}
            & \\text{نحن حمد بن عيسى آل خليفة ملك مملكة البحرين}
            \\end{aligned}$$
            
            الباب الأول
            تعاريف وأحكام عامة""",
            
            """المادة (1)
            في تطبيق أحكام هذا القانون، يكون للكلمات والعبارات التالية المعاني المبينة قرين كل منها.
            
            المادة (2)
            يسري هذا القانون على جميع العمال وأصحاب الأعمال في القطاع الأهلي."""
        ]
        
        # معالجة للتخزين في قاعدة البيانات
        result = advanced_processor.process_for_database_storage(sample_pages, "test_integration.pdf")
        
        # فحص النتائج
        checks = {
            'document_data': result['document'] is not None,
            'pages_data': len(result['pages']) > 0,
            'indexing_data': len(result['indexing']) > 0,
            'title_extracted': result['document'].get('extracted_title') is not None,
            'quality_calculated': result['document'].get('content_quality_score', 0) > 0
        }
        
        passed_checks = sum(checks.values())
        total_checks = len(checks)
        
        print(f"   📊 نتائج فحص التكامل:")
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"      {status} {check_name}")
        
        if passed_checks == total_checks:
            print("   🎉 التكامل يعمل بشكل مثالي!")
            return True
        else:
            print(f"   ⚠️ التكامل يعمل جزئياً ({passed_checks}/{total_checks})")
            return False
            
    except Exception as e:
        print(f"   ❌ خطأ في اختبار التكامل: {e}")
        return False

def test_performance():
    """اختبار الأداء"""
    print("\n⚡ اختبار الأداء...")
    
    try:
        import time
        from content_cleaner import content_cleaner
        from title_extractor import title_extractor
        from legal_indexer import legal_indexer
        
        # نص تجريبي كبير
        large_text = """
        قانون رقم (36) لسنة 2012 بإصدار قانون العمل في القطاع الأهلي
        
        الباب الأول - تعاريف وأحكام عامة
        الفصل الأول - تعاريف
        """ * 100  # تكرار لمحاكاة نص كبير
        
        # اختبار سرعة التنظيف
        start_time = time.time()
        cleaning_result = content_cleaner.clean_content(large_text)
        cleaning_time = time.time() - start_time
        
        # اختبار سرعة الفهرسة
        start_time = time.time()
        indexing_result = legal_indexer.create_comprehensive_index(large_text)
        indexing_time = time.time() - start_time
        
        print(f"   ⏱️ وقت التنظيف: {cleaning_time:.3f} ثانية")
        print(f"   ⏱️ وقت الفهرسة: {indexing_time:.3f} ثانية")
        print(f"   📏 حجم النص: {len(large_text)} حرف")
        print(f"   🔤 الكلمات المستخرجة: {len(indexing_result['keywords'])}")
        
        if cleaning_time < 2.0 and indexing_time < 3.0:
            print("   ✅ الأداء ممتاز!")
            return True
        else:
            print("   ⚠️ الأداء مقبول لكن يمكن تحسينه")
            return False
            
    except Exception as e:
        print(f"   ❌ خطأ في اختبار الأداء: {e}")
        return False

def main():
    """الدالة الرئيسية للاختبار"""
    print("🧪 بدء اختبار النظام المحسن الشامل")
    print("=" * 60)
    
    # اختبار البيئة الأساسية
    print("🔍 اختبار البيئة الأساسية...")
    if not os.getenv("MISTRAL_API_KEY") and not os.getenv("SUPABASE_URL"):
        print("   ⚠️ بعض متغيرات البيئة مفقودة - سيتم استخدام القيم الاحتياطية")
    else:
        print("   ✅ متغيرات البيئة متوفرة")
    
    # تشغيل الاختبارات
    results = {}
    
    # اختبار المكونات المحسنة
    enhanced_passed, enhanced_total = test_enhanced_components()
    results['enhanced_components'] = (enhanced_passed, enhanced_total)
    
    # اختبار قاعدة البيانات
    db_result = test_database_enhancements()
    results['database'] = (1 if db_result else 0, 1)
    
    # اختبار التكامل
    integration_result = test_integration()
    results['integration'] = (1 if integration_result else 0, 1)
    
    # اختبار الأداء
    performance_result = test_performance()
    results['performance'] = (1 if performance_result else 0, 1)
    
    # تقرير النتائج النهائي
    print("\n" + "=" * 60)
    print("📊 تقرير الاختبار الشامل:")
    
    total_passed = 0
    total_tests = 0
    
    for test_name, (passed, total) in results.items():
        total_passed += passed
        total_tests += total
        percentage = (passed / total * 100) if total > 0 else 0
        status = "✅" if percentage == 100 else "⚠️" if percentage >= 50 else "❌"
        print(f"   {status} {test_name}: {passed}/{total} ({percentage:.1f}%)")
    
    overall_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n🎯 النتيجة الإجمالية: {total_passed}/{total_tests} ({overall_percentage:.1f}%)")
    
    if overall_percentage >= 90:
        print("🎉 النظام المحسن جاهز للاستخدام بكامل طاقته!")
        print("\n💡 الخطوات التالية:")
        print("   1. شغل السكربت enhanced_database_schema.sql في Supabase")
        print("   2. ضع ملفات PDF في مجلد 'docs_import'")
        print("   3. شغل: python BatchPdfConv_SuperEnhanced.py")
    elif overall_percentage >= 70:
        print("✅ النظام المحسن يعمل بشكل جيد مع بعض التحسينات الممكنة")
        print("   يمكنك استخدامه لكن راجع الأخطاء أعلاه")
    else:
        print("⚠️ النظام المحسن يحتاج إلى إصلاحات قبل الاستخدام")
        print("   يرجى إصلاح المشاكل المذكورة أعلاه")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
