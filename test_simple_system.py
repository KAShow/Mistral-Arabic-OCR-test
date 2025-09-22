"""
اختبار النظام المبسط
اختبار سريع للتأكد من عمل المكونات الأساسية
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_basic_components():
    """اختبار المكونات الأساسية"""
    print("🔍 اختبار المكونات الأساسية...")
    
    tests_passed = 0
    tests_total = 3
    
    # اختبار تنظيف المحتوى
    print("\n🧹 اختبار تنظيف المحتوى...")
    try:
        from content_cleaner import content_cleaner
        
        test_text = """
        ![img-0.jpeg](img-0.jpeg)
        # قانون العمل في القطاع الأهلي
        $$\\begin{aligned}\\text{نص تجريبي}\\end{aligned}$$
        هذا نص عربي يجب أن يبقى.
        """
        
        result = content_cleaner.clean_content(test_text)
        
        if result['is_useful'] and 'قانون العمل' in result['cleaned_text']:
            print("   ✅ تنظيف المحتوى يعمل بشكل صحيح")
            tests_passed += 1
        else:
            print("   ❌ مشكلة في تنظيف المحتوى")
            
    except Exception as e:
        print(f"   ❌ خطأ في تنظيف المحتوى: {e}")
    
    # اختبار استخراج العناوين
    print("\n📝 اختبار استخراج العناوين...")
    try:
        from title_extractor import title_extractor
        
        test_pages = [
            "![img-0.jpeg](img-0.jpeg)",
            "قانون رقم (36) لسنة 2012\nبإصدار قانون العمل في القطاع الأهلي"
        ]
        
        result = title_extractor.extract_title_from_pages(test_pages)
        
        if result['title'] and 'قانون' in result['title']:
            print(f"   ✅ استخراج العناوين يعمل: {result['full_title']}")
            tests_passed += 1
        else:
            print("   ❌ مشكلة في استخراج العناوين")
            
    except Exception as e:
        print(f"   ❌ خطأ في استخراج العناوين: {e}")
    
    # اختبار قاعدة البيانات
    print("\n💾 اختبار قاعدة البيانات...")
    try:
        from supabase_client import db_manager
        
        if db_manager:
            docs = db_manager.get_all_documents()
            print(f"   ✅ الاتصال بقاعدة البيانات يعمل - {len(docs)} وثيقة موجودة")
            tests_passed += 1
        else:
            print("   ❌ فشل في الاتصال بقاعدة البيانات")
            
    except Exception as e:
        print(f"   ❌ خطأ في قاعدة البيانات: {e}")
    
    return tests_passed, tests_total

def test_simple_processor():
    """اختبار المعالج المبسط"""
    print("\n🔧 اختبار المعالج المبسط...")
    
    try:
        from BatchPdfConv_Simple import SimplePDFProcessor
        
        # تهيئة المعالج
        processor = SimplePDFProcessor()
        
        # اختبار إنشاء الكلمات المفتاحية
        test_text = "قانون العمل في القطاع الأهلي يحتوي على مواد قانونية مهمة للعمال وأصحاب الأعمال"
        keywords = processor.create_enhanced_keywords(test_text)
        
        if len(keywords) > 0 and any('قانون' in word or 'العمل' in word for word in keywords):
            print(f"   ✅ إنشاء الكلمات المفتاحية يعمل - {len(keywords)} كلمة")
            return True
        else:
            print("   ❌ مشكلة في إنشاء الكلمات المفتاحية")
            return False
            
    except Exception as e:
        print(f"   ❌ خطأ في المعالج المبسط: {e}")
        return False

def test_database_update():
    """اختبار تحديث قاعدة البيانات"""
    print("\n📊 فحص تحديث قاعدة البيانات...")
    
    try:
        from supabase_client import db_manager
        
        if not db_manager:
            print("   ❌ عميل قاعدة البيانات غير متاح")
            return False
        
        # محاولة جلب الوثائق مع الحقول الجديدة
        docs = db_manager.get_all_documents()
        
        if docs:
            # فحص وجود الحقول الجديدة في أول وثيقة
            first_doc = docs[0]
            has_extracted_title = 'extracted_title' in first_doc
            has_document_type = 'document_type' in first_doc
            
            if has_extracted_title and has_document_type:
                print("   ✅ الحقول الجديدة موجودة في قاعدة البيانات")
                return True
            else:
                print("   ⚠️ الحقول الجديدة غير موجودة - يرجى تشغيل simple_database_update.sql")
                return False
        else:
            print("   ℹ️ لا توجد وثائق في قاعدة البيانات حالياً")
            return True
            
    except Exception as e:
        print(f"   ❌ خطأ في فحص قاعدة البيانات: {e}")
        return False

def main():
    """الدالة الرئيسية للاختبار"""
    print("🧪 اختبار النظام المبسط")
    print("=" * 40)
    
    # فحص متغيرات البيئة
    print("🔍 فحص متغيرات البيئة...")
    mistral_key = os.getenv("MISTRAL_API_KEY")
    supabase_url = os.getenv("SUPABASE_URL")
    
    if mistral_key or supabase_url:
        print("   ✅ متغيرات البيئة متوفرة")
    else:
        print("   ⚠️ سيتم استخدام القيم الاحتياطية")
    
    # تشغيل الاختبارات
    results = {}
    
    # اختبار المكونات الأساسية
    basic_passed, basic_total = test_basic_components()
    results['basic'] = (basic_passed, basic_total)
    
    # اختبار المعالج المبسط
    processor_result = test_simple_processor()
    results['processor'] = (1 if processor_result else 0, 1)
    
    # اختبار قاعدة البيانات
    db_result = test_database_update()
    results['database'] = (1 if db_result else 0, 1)
    
    # النتائج النهائية
    print("\n" + "=" * 40)
    print("📊 تقرير الاختبار:")
    
    total_passed = 0
    total_tests = 0
    
    for test_name, (passed, total) in results.items():
        total_passed += passed
        total_tests += total
        percentage = (passed / total * 100) if total > 0 else 0
        status = "✅" if percentage == 100 else "⚠️" if percentage >= 50 else "❌"
        print(f"   {status} {test_name}: {passed}/{total} ({percentage:.0f}%)")
    
    overall_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n🎯 النتيجة الإجمالية: {total_passed}/{total_tests} ({overall_percentage:.0f}%)")
    
    if overall_percentage >= 80:
        print("\n🎉 النظام المبسط جاهز للاستخدام!")
        print("\n📋 الخطوات التالية:")
        print("   1. شغل: simple_database_update.sql في Supabase (إذا لم تفعل)")
        print("   2. ضع ملفات PDF في مجلد 'docs_import'")
        print("   3. شغل: python BatchPdfConv_Simple.py")
        print("\n✨ النتيجة المتوقعة:")
        print("   من: (img-0.jpeg)(img-0.jpeg)!")
        print("   إلى: قانون العمل في القطاع الأهلي - قانون رقم (٣٦) لسنة ٢٠١٢")
    else:
        print("\n⚠️ يرجى إصلاح المشاكل أعلاه قبل الاستخدام")
        if results['database'][0] == 0:
            print("   💡 تلميح: شغل simple_database_update.sql في Supabase")
    
    print("=" * 40)

if __name__ == '__main__':
    main()
