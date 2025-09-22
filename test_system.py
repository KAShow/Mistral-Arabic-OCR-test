"""
سكربت اختبار شامل للنظام
يختبر الاتصال مع Supabase والفهرسة والمعالجة
"""

import os
import sys
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

def test_environment_variables():
    """اختبار متغيرات البيئة المطلوبة"""
    print("🔍 اختبار متغيرات البيئة...")
    
    required_vars = {
        'MISTRAL_API_KEY': 'مفتاح Mistral AI',
        'SUPABASE_URL': 'رابط Supabase',
        'SUPABASE_KEY': 'مفتاح Supabase'
    }
    
    # القيم الاحتياطية المدمجة
    fallback_values = {
        'MISTRAL_API_KEY': '97ZQlsV45YrDusgZRwjArWGbh3nerFPb',
        'SUPABASE_URL': 'https://fdnruljygqbpidrspyyl.supabase.co',
        'SUPABASE_KEY': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZkbnJ1bGp5Z3FicGlkcnNweXlsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1ODU2MzIsImV4cCI6MjA3MzE2MTYzMn0.ZPbraTaW7InlPCiuD8kIsi7ZogSqzbmj1iw3vXAmxHQ'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            if var in fallback_values:
                print(f"   ⚠️ {var} غير موجود في .env - سيتم استخدام القيمة المدمجة")
            else:
                missing_vars.append(f"   ❌ {var} ({description})")
                print(f"   ❌ {var} غير موجود")
        else:
            print(f"   ✅ {var} موجود في .env")
    
    if missing_vars:
        print("\n⚠️ متغيرات البيئة المفقودة:")
        for var in missing_vars:
            print(var)
        return False
    
    print("   ✅ جميع المتغيرات متوفرة (من .env أو القيم المدمجة)")
    return True

def test_supabase_connection():
    """اختبار الاتصال مع Supabase"""
    print("\n🔍 اختبار الاتصال مع Supabase...")
    
    try:
        from supabase_client import db_manager
        
        if not db_manager:
            print("   ❌ فشل في تهيئة عميل Supabase")
            return False
        
        # اختبار الاتصال بجلب الوثائق
        docs = db_manager.get_all_documents()
        print(f"   ✅ تم الاتصال بنجاح - عدد الوثائق الموجودة: {len(docs)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ في الاتصال مع Supabase: {e}")
        return False

def test_text_indexer():
    """اختبار نظام الفهرسة"""
    print("\n🔍 اختبار نظام الفهرسة...")
    
    try:
        from text_indexer import text_indexer
        
        # نص تجريبي
        test_text = """
        هذا نص تجريبي للاختبار. يحتوي على كلمات عربية مختلفة.
        سيتم استخراج الكلمات المفتاحية من هذا النص.
        النظام يجب أن يتعامل مع النصوص العربية بشكل صحيح.
        """
        
        # اختبار استخراج الكلمات
        words = text_indexer.extract_words(test_text)
        print(f"   ✅ استخراج الكلمات: {len(words)} كلمة")
        
        # اختبار استخراج الكلمات المفتاحية
        keywords = text_indexer.extract_keywords(test_text, 5)
        print(f"   ✅ الكلمات المفتاحية: {keywords}")
        
        # اختبار تقسيم النص
        chunks = text_indexer.chunk_text(test_text)
        print(f"   ✅ تقسيم النص: {len(chunks)} جزء")
        
        # اختبار الفهرس الشامل
        full_index = text_indexer.create_full_index(test_text)
        print(f"   ✅ الفهرس الشامل: {full_index['statistics']['total_words']} كلمة إجمالية")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ في نظام الفهرسة: {e}")
        return False

def test_mistral_api():
    """اختبار API Mistral"""
    print("\n🔍 اختبار Mistral API...")
    
    try:
        from mistralai import Mistral
        
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            # استخدام المفتاح الاحتياطي
            api_key = "97ZQlsV45YrDusgZRwjArWGbh3nerFPb"
            print("   ⚠️ استخدام مفتاح Mistral API الاحتياطي المدمج")
        else:
            print("   ✅ مفتاح Mistral API موجود في .env")
        
        client = Mistral(api_key=api_key)
        print("   ✅ تم تهيئة عميل Mistral بنجاح")
        
        # ملاحظة: لا نقوم باختبار فعلي للـ OCR لتوفير الاستخدام
        print("   ℹ️  لم يتم اختبار OCR الفعلي (لتوفير الاستخدام)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ في Mistral API: {e}")
        return False

def test_directories():
    """اختبار وجود المجلدات المطلوبة"""
    print("\n🔍 اختبار المجلدات...")
    
    required_dirs = ['docs_import', 'docs_exports']
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"   ✅ {directory} موجود")
        else:
            print(f"   ⚠️ {directory} غير موجود - سيتم إنشاؤه تلقائياً")
    
    return True

def test_sample_database_operations():
    """اختبار عمليات قاعدة البيانات الأساسية"""
    print("\n🔍 اختبار عمليات قاعدة البيانات...")
    
    try:
        from supabase_client import db_manager
        
        if not db_manager:
            print("   ❌ عميل قاعدة البيانات غير متاح")
            return False
        
        # اختبار البحث عن ملف غير موجود
        result = db_manager.get_document_by_filename("test_nonexistent.pdf")
        if result is None:
            print("   ✅ البحث عن ملف غير موجود يعمل بشكل صحيح")
        
        # اختبار جلب جميع الوثائق
        all_docs = db_manager.get_all_documents()
        print(f"   ✅ جلب الوثائق: {len(all_docs)} وثيقة موجودة")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ في عمليات قاعدة البيانات: {e}")
        return False

def main():
    """الدالة الرئيسية للاختبار"""
    print("🧪 بدء اختبار النظام الشامل")
    print("=" * 50)
    
    tests = [
        ("متغيرات البيئة", test_environment_variables),
        ("الاتصال مع Supabase", test_supabase_connection),
        ("نظام الفهرسة", test_text_indexer),
        ("Mistral API", test_mistral_api),
        ("المجلدات", test_directories),
        ("عمليات قاعدة البيانات", test_sample_database_operations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"   💥 خطأ غير متوقع في {test_name}: {e}")
            results.append((test_name, False))
    
    # تقرير النتائج
    print("\n" + "=" * 50)
    print("📊 تقرير الاختبار النهائي:")
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ نجح" if success else "❌ فشل"
        print(f"   {status}: {test_name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 النتيجة: {passed} نجح، {failed} فشل من أصل {len(results)}")
    
    if failed == 0:
        print("🎉 جميع الاختبارات نجحت! النظام جاهز للاستخدام")
        print("\n💡 الخطوات التالية:")
        print("   1. ضع ملفات PDF في مجلد 'docs_import'")
        print("   2. شغل: python BatchPdfConv_Enhanced.py")
    else:
        print("⚠️ يرجى إصلاح المشاكل المذكورة أعلاه قبل استخدام النظام")
    
    print("=" * 50)

if __name__ == '__main__':
    main()
