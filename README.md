# معالج PDF العربي مع التخزين المحلي JSON

## الوصف
معالج PDF محسن يستخدم Mistral OCR لاستخراج النصوص العربية من ملفات PDF وحفظها محلياً بصيغة JSON.

## المميزات الجديدة
- ✅ تخزين محلي كامل بدلاً من قاعدة البيانات
- 💾 حفظ البيانات في ملفات JSON منظمة
- 🗂️ هيكل مجلدات واضح ومنظم
- 📊 فهرسة ذكية للنصوص العربية
- 🚫 لا يتطلب اتصال بالإنترنت للتخزين

## التثبيت
```bash
pip install -r requirements.txt
```

## البنية الجديدة للملفات
```
json_data/
├── metadata.json          # البيانات الوصفية الرئيسية
├── documents/             # بيانات الوثائق
│   ├── document_id_1.json
│   └── document_id_2.json
├── content/               # محتوى الصفحات
│   ├── document_id_page_001.json
│   └── document_id_page_002.json
├── indexes/               # الفهارس
│   ├── document_id_chunk_001.json
│   └── document_id_chunk_002.json
└── filename_complete.json # الوثيقة الكاملة
```

## الاستخدام

### معالجة جميع الملفات
```bash
python BatchPdfConv_Enhanced.py
```

### معالجة ملف واحد
```bash
python BatchPdfConv_Enhanced.py --single-file "filename.pdf"
```

### عرض الإحصائيات
```bash
python BatchPdfConv_Enhanced.py --status
```

## أنواع البيانات المحفوظة

### 1. ملف الوثيقة الكاملة
يحتوي على جميع البيانات المستخرجة في ملف واحد:
- النص الكامل
- بيانات كل صفحة
- الفهارس والكلمات المفتاحية
- الإحصائيات

### 2. ملفات منفصلة
- `documents/`: معلومات أساسية عن كل وثيقة
- `content/`: محتوى كل صفحة منفصلة
- `indexes/`: فهارس البحث لكل جزء من النص

## التغييرات عن الإصدار السابق
- ❌ إزالة اتصال Supabase
- ❌ إزالة ملفات Markdown
- ✅ إضافة نظام التخزين المحلي JSON
- ✅ تحسين هيكل البيانات
- ✅ تبسيط المتطلبات

## الملفات المطلوبة
- `BatchPdfConv_Enhanced.py` - المعالج الرئيسي
- `json_storage.py` - نظام التخزين المحلي
- `text_indexer.py` - فهرسة النصوص العادية
- `legal_indexer.py` - فهرسة النصوص القانونية
- `requirements.txt` - المتطلبات

## متغيرات البيئة
```
MISTRAL_API_KEY=your_api_key_here
```

## النتائج
بعد المعالجة ستجد:
- مجلد `json_data/` يحتوي على جميع البيانات
- ملفات JSON منظمة وقابلة للقراءة
- إمكانية البحث والتصفح محلياً
- عدم الحاجة لاتصال الإنترنت للوصول للبيانات
