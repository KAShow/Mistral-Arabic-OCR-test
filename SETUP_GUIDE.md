# 🚀 دليل إعداد نظام OCR + Supabase

## 📋 نظرة عامة

تم تطوير النظام ليشمل:
- **OCR متقدم** باستخدام Mistral AI
- **فهرسة ذكية** للنصوص العربية
- **تخزين في Supabase** قاعدة بيانات حية
- **معالجة دفعية** محسنة

---

## ⚙️ خطوات الإعداد

### 1. تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

### 2. إعداد متغيرات البيئة

أنشئ ملف `.env` في المجلد الرئيسي:

```env
# مفتاح Mistral AI
MISTRAL_API_KEY="your_mistral_api_key_here"

# إعدادات Supabase
SUPABASE_URL="https://fdnruljygqbpidrspyyl.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZkbnJ1bGp5Z3FicGlkcnNweXlsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1ODU2MzIsImV4cCI6MjA3MzE2MTYzMn0.ZPbraTaW7InlPCiuD8kIsi7ZogSqzbmj1iw3vXAmxHQ"
```

### 3. إعداد قاعدة البيانات في Supabase

تأكد من إنشاء الجداول التالية في Supabase:

```sql
-- جدول الوثائق الرئيسي
CREATE TABLE documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    filename TEXT NOT NULL,
    original_path TEXT,
    file_size BIGINT,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'completed', 'failed')),
    metadata JSONB DEFAULT '{}'
);

-- جدول المحتوى المستخرج
CREATE TABLE document_content (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER,
    raw_markdown TEXT,
    processed_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- جدول الفهرسة والبحث
CREATE TABLE document_index (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    content_chunk TEXT,
    keywords TEXT[],
    chunk_position INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- فهارس للبحث السريع
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_upload_date ON documents(upload_date);
CREATE INDEX idx_content_document_id ON document_content(document_id);
CREATE INDEX idx_index_keywords ON document_index USING GIN(keywords);
```

---

## 🧪 اختبار النظام

قبل البدء، اختبر النظام:

```bash
python test_system.py
```

يجب أن ترى:
```
🎉 جميع الاختبارات نجحت! النظام جاهز للاستخدام
```

---

## 🚀 استخدام النظام

### الطريقة الجديدة (مع Supabase):

```bash
python BatchPdfConv_Enhanced.py
```

**الميزات:**
- ✅ حفظ في قاعدة البيانات الحية
- ✅ فهرسة تلقائية للنصوص
- ✅ تتبع حالة المعالجة
- ✅ إعادة المحاولة التلقائية
- ✅ إحصائيات مفصلة

### الطريقة القديمة (ملفات محلية فقط):

```bash
python BatchPdfConv.py
```

---

## 📁 هيكل الملفات

```
المشروع/
├── docs_import/           # ضع ملفات PDF هنا
├── docs_exports/          # ملفات Markdown المُصدرة
├── supabase_client.py     # عميل قاعدة البيانات
├── text_indexer.py        # نظام الفهرسة
├── BatchPdfConv_Enhanced.py  # المعالج المحسن
├── test_system.py         # اختبار النظام
├── requirements.txt       # المتطلبات
└── .env                   # متغيرات البيئة
```

---

## 📊 ما يحدث في النظام الجديد

1. **رفع الملف**: يتم تسجيل الملف في جدول `documents`
2. **OCR**: استخراج النص باستخدام Mistral AI
3. **حفظ المحتوى**: كل صفحة تُحفظ في `document_content`
4. **الفهرسة**: استخراج الكلمات المفتاحية وتقسيم النص
5. **التخزين**: الفهارس تُحفظ في `document_index`
6. **النسخ الاحتياطي**: ملف Markdown محلي

---

## 🔍 البحث في البيانات

البحث سيكون منفصلاً عن Python كما طلبت. يمكنك:

1. **استخدام Supabase Dashboard** للبحث المباشر
2. **إنشاء تطبيق ويب** منفصل للبحث
3. **استخدام SQL مباشرة** للاستعلامات المعقدة

### أمثلة استعلامات SQL:

```sql
-- البحث في أسماء الملفات
SELECT * FROM documents WHERE filename ILIKE '%قانون%';

-- البحث في المحتوى
SELECT d.filename, dc.page_number, dc.raw_markdown 
FROM documents d 
JOIN document_content dc ON d.id = dc.document_id 
WHERE dc.raw_markdown ILIKE '%العمل%';

-- البحث بالكلمات المفتاحية
SELECT d.filename, di.content_chunk 
FROM documents d 
JOIN document_index di ON d.id = di.document_id 
WHERE 'قانون' = ANY(di.keywords);
```

---

## ⚡ الخطوة الأولى الآن

1. **أنشئ ملف `.env`** بالمتغيرات المطلوبة
2. **شغل اختبار النظام**: `python test_system.py`
3. **ضع ملفات PDF في `docs_import/`**
4. **شغل المعالج**: `python BatchPdfConv_Enhanced.py`

---

## 🎯 النتيجة المتوقعة

بعد المعالجة ستحصل على:
- 📄 **ملفات Markdown محلية** (نسخ احتياطية)
- 🗄️ **بيانات منظمة في Supabase** (قابلة للبحث)
- 🔍 **فهارس ذكية** للبحث السريع
- 📊 **إحصائيات مفصلة** عن المعالجة
