"""
اختبار تحديد طول العناوين - التأكد من عدم تجاوز 10 كلمات
"""

from title_extractor import title_extractor

def test_title_word_limit():
    """اختبار تحديد طول العناوين"""
    print("🔍 اختبار تحديد طول العناوين...")
    
    # اختبار عنوان طويل
    long_title = "قانون رقم ثلاثة وستون لسنة ألفين واثني عشر بإصدار قانون العمل في القطاع الأهلي والخاص والحكومي"
    
    # تحديد طول العنوان
    limited_title = title_extractor.limit_title_words(long_title, 10)
    
    print(f"العنوان الأصلي: {long_title}")
    print(f"عدد الكلمات الأصلي: {len(long_title.split())}")
    print(f"العنوان المحدود: {limited_title}")
    print(f"عدد الكلمات المحدود: {len(limited_title.replace('...', '').split())}")
    
    # التحقق من النتيجة
    limited_words = limited_title.replace('...', '').split()
    if len(limited_words) <= 10:
        print("✅ تحديد طول العنوان يعمل بشكل صحيح")
        return True
    else:
        print("❌ تحديد طول العنوان لا يعمل")
        return False

def test_with_real_content():
    """اختبار مع محتوى حقيقي"""
    print("\n🔍 اختبار مع محتوى حقيقي...")
    
    # محتوى تجريبي طويل
    test_pages = [
        "![img-0.jpeg](img-0.jpeg)",
        """قانون رقم (36) لسنة 2012
        بإصدار قانون العمل في القطاع الأهلي والخاص
        
        نحن حمد بن عيسى آل خليفة ملك مملكة البحرين
        بعد الاطلاع على الدستور وعلى قانون المرافعات المدنية والتجارية"""
    ]
    
    # استخراج العنوان
    result = title_extractor.extract_title_from_pages(test_pages)
    
    if result and result['full_title']:
        title = result['full_title']
        word_count = len(title.split())
        
        print(f"العنوان المستخرج: {title}")
        print(f"عدد الكلمات: {word_count}")
        
        if word_count <= 10:
            print("✅ العنوان المستخرج ضمن الحد المسموح")
            return True
        else:
            print("❌ العنوان المستخرج يتجاوز 10 كلمات")
            return False
    else:
        print("⚠️ لم يتم استخراج عنوان")
        return False

def main():
    """الدالة الرئيسية للاختبار"""
    print("🧪 اختبار تحديد طول العناوين (أقصى 10 كلمات)")
    print("=" * 50)
    
    # اختبار التحديد المباشر
    test1 = test_title_word_limit()
    
    # اختبار مع المحتوى الحقيقي
    test2 = test_with_real_content()
    
    print("\n" + "=" * 50)
    print("📊 نتائج الاختبار:")
    print(f"   {'✅' if test1 else '❌'} تحديد طول العنوان")
    print(f"   {'✅' if test2 else '❌'} استخراج عنوان محدود")
    
    if test1 and test2:
        print("\n🎉 جميع الاختبارات نجحت!")
        print("✅ العناوين ستكون محدودة بـ 10 كلمات كحد أقصى")
    else:
        print("\n⚠️ بعض الاختبارات فشلت")
    
    print("=" * 50)

if __name__ == '__main__':
    main()
