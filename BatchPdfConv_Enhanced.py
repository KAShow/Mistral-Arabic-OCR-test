"""
معالج PDF محسن مع دعم التخزين المحلي والفهرسة الذكية
يدمج OCR مع التخزين المحلي والفهرسة التلقائية
"""

import os
import sys
import base64
import time
import logging
from pathlib import Path
from datetime import datetime
from mistralai import Mistral
from dotenv import load_dotenv
from tqdm import tqdm

# استيراد الوحدات المخصصة
from json_storage import json_storage
from text_indexer import text_indexer

load_dotenv()

# Configuration
DOC_DIR = "docs_import"
EXPORT_DIR = "docs_exports"
LOG_FILE = "supabase_conversion.log"
DETAILED_LOG = "detailed_processing_log.txt"
MAX_RETRIES = 5
INITIAL_BACKOFF = 1  # in seconds

class ArabicFileLogger:
    """مسجل ملفات يدعم العربية"""
    
    def __init__(self, log_file):
        self.log_file = log_file
        self.start_time = datetime.now()
        
        # إنشاء ملف السجل مع دعم UTF-8
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("📋 سجل معالجة PDF المفصل\n")
            f.write(f"🕐 بدء التسجيل: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
    
    def log(self, message, level="INFO"):
        """تسجيل رسالة مع الوقت"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_line = f"[{timestamp}] {level}: {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line)
        
        # طباعة على الشاشة أيضاً
        print(message)
    
    def log_separator(self, title=""):
        """تسجيل فاصل"""
        separator = "-" * 50
        if title:
            separator += f" {title} " + "-" * 10
        
        self.log(separator)

# إنشاء مسجل الملفات
file_logger = ArabicFileLogger(DETAILED_LOG)

# Initialize logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
)

# Ensure API key is set via environment variable
API_KEY = os.getenv("MISTRAL_API_KEY")
if not API_KEY:
    # استخدام مفتاح احتياطي مدمج
    API_KEY = "97ZQlsV45YrDusgZRwjArWGbh3nerFPb"
    print("⚠️ استخدام مفتاح Mistral API الاحتياطي المدمج")

if not API_KEY:
    print("❌ خطأ: لم يتم تعيين MISTRAL_API_KEY في متغيرات البيئة")
    sys.exit(1)

client = Mistral(api_key=API_KEY)

class EnhancedPDFProcessor:
    """معالج PDF محسن مع دعم التخزين المحلي"""
    
    def __init__(self):
        """تهيئة المعالج"""
        self.ensure_directories()
        
        # التحقق من نظام التخزين المحلي
        if not json_storage:
            print("❌ خطأ: فشل في تهيئة نظام التخزين المحلي")
            sys.exit(1)
        
        print("✅ تم تهيئة المعالج بنجاح")
        print("💾 التخزين المحلي بصيغة JSON مفعل")
    
    def ensure_directories(self):
        """التأكد من وجود المجلدات المطلوبة"""
        for directory in [DOC_DIR, EXPORT_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"✅ تم إنشاء المجلد: {directory}")
    
    def get_pdf_files(self):
        """الحصول على جميع ملفات PDF في المجلد"""
        if not os.path.isdir(DOC_DIR):
            print(f"❌ خطأ: المجلد '{DOC_DIR}' غير موجود")
            sys.exit(1)
        
        pdf_files = []
        for root, dirs, files in os.walk(DOC_DIR):
            for file in files:
                if file.lower().endswith('.pdf'):
                    rel_path = os.path.relpath(os.path.join(root, file), DOC_DIR)
                    pdf_files.append(rel_path)
        
        return pdf_files
    
    def encode_pdf(self, pdf_path):
        """ترميز ملف PDF إلى base64 مع التحقق من السلامة"""
        try:
            file_logger.log(f"🔄 قراءة الملف من: {pdf_path}")
            with open(pdf_path, "rb") as pdf_file:
                pdf_content = pdf_file.read()
            
            file_logger.log(f"✅ تم قراءة {len(pdf_content):,} بايت")
                
            # التحقق من صحة الملف
            if len(pdf_content) == 0:
                raise ValueError("الملف فارغ")
                
            if not pdf_content.startswith(b'%PDF'):
                raise ValueError("الملف ليس PDF صالح")
            
            file_logger.log("🔄 بدء ترميز base64...")
            
            # ترميز base64
            encoded = base64.b64encode(pdf_content).decode('utf-8')
            
            file_logger.log(f"✅ تم الترميز - الطول: {len(encoded):,} حرف")
            
            # التحقق من صحة base64
            if not encoded or len(encoded) < 100:
                raise ValueError("فشل في ترميز base64 بشكل صحيح")
            
            # اختبار فك الترميز للتأكد
            file_logger.log("🔍 اختبار فك ترميز base64...")
            try:
                decoded_test = base64.b64decode(encoded)
                if len(decoded_test) != len(pdf_content):
                    raise ValueError("base64 لا يطابق الملف الأصلي")
                file_logger.log("✅ اختبار فك الترميز نجح")
            except Exception as decode_error:
                file_logger.log(f"❌ فشل اختبار فك الترميز: {decode_error}", "ERROR")
                raise ValueError("base64 تالف - فشل في فك الترميز")
            
            file_logger.log(f"📏 ملخص الترميز:")
            file_logger.log(f"   📄 حجم الملف الأصلي: {len(pdf_content):,} بايت")
            file_logger.log(f"   📝 طول base64: {len(encoded):,} حرف")
            file_logger.log(f"   📊 نسبة الضغط: {len(encoded)/len(pdf_content):.2f}x")
            
            return encoded
            
        except Exception as e:
            file_logger.log(f"❌ فشل في ترميز {pdf_path}: {e}", "ERROR")
            logging.error(f"فشل في ترميز {pdf_path}: {e}")
            return None
    
    def get_file_size(self, file_path):
        """الحصول على حجم الملف"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logging.error(f"فشل في الحصول على حجم الملف {file_path}: {e}")
            return 0
    
    def process_pdf_with_ocr(self, pdf_filename):
        """معالجة PDF باستخدام OCR وحفظ النتائج محلياً في JSON"""
        full_path = os.path.join(DOC_DIR, pdf_filename)
        
        # تسجيل بداية المعالجة
        file_logger.log_separator(f"معالجة {pdf_filename}")
        file_logger.log(f"🚀 بدء معالجة الملف: {pdf_filename}")
        file_logger.log(f"📂 المسار الكامل: {full_path}")
        
        # فحص شامل للملف
        try:
            file_logger.log("🔍 فحص وجود الملف...")
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"الملف غير موجود: {full_path}")
            
            file_logger.log("✅ الملف موجود")
            
            # فحص حجم الملف
            file_size = os.path.getsize(full_path)
            file_logger.log(f"📏 حجم الملف: {file_size:,} بايت ({file_size/1024/1024:.2f} MB)")
            
            if file_size == 0:
                raise ValueError("الملف فارغ")
            
            if file_size > 500 * 1024 * 1024:  # 50MB
                raise ValueError(f"الملف كبير جداً: {file_size/1024/1024:.1f} MB (الحد الأقصى: 500 MB)")
            
            # فحص نوع الملف
            file_logger.log("🔍 فحص صيغة PDF...")
            with open(full_path, 'rb') as f:
                first_bytes = f.read(10)
                if not first_bytes.startswith(b'%PDF'):
                    raise ValueError("الملف ليس PDF صالح")
            
            file_logger.log("✅ الملف PDF صالح")
            
            # فحص قابلية القراءة
            file_logger.log("🔍 اختبار قراءة الملف كاملاً...")
            with open(full_path, 'rb') as f:
                content = f.read()
                if len(content) != file_size:
                    raise ValueError("فشل في قراءة الملف كاملاً")
            
            file_logger.log("✅ تم قراءة الملف بنجاح")
            
        except Exception as e:
            file_logger.log(f"❌ فشل في فحص الملف: {str(e)}", "ERROR")
            raise
        
        # التحقق من وجود الملف في النظام المحلي
        file_logger.log("🔍 فحص التخزين المحلي...")
        existing_doc = json_storage.get_document_by_filename(pdf_filename)
        if existing_doc and existing_doc['status'] == 'completed':
            file_logger.log(f"⚠️ الملف {pdf_filename} تم معالجته مسبقاً")
            return existing_doc['id']
        
        file_logger.log("✅ الملف جاهز للمعالجة")
        
        # إنشاء سجل الوثيقة في النظام المحلي
        if existing_doc:
            document_id = existing_doc['id']
            json_storage.update_document_status(document_id, 'processing')
        else:
            # إنشاء سجل محلي جديد
            document_id = json_storage.create_document(
                filename=pdf_filename,
                original_path=full_path,
                file_size=file_size,
                metadata={'processor': 'mistral-ocr-latest', 'local_storage': True}
            )
            json_storage.update_document_status(document_id, 'processing')
        
        try:
            # ترميز PDF
            file_logger.log("🔄 بدء ترميز PDF إلى base64...")
            b64 = self.encode_pdf(full_path)
            if not b64:
                raise RuntimeError("فشل في ترميز PDF")
            
            file_logger.log(f"✅ تم ترميز PDF بنجاح - الطول: {len(b64):,} حرف")
            file_logger.log(f"🔄 معالجة OCR للملف: {pdf_filename}")
            
            # التحقق من حجم base64 قبل الإرسال
            max_size_mb = 50  # حد أقصى 50 ميجا
            max_size_chars = max_size_mb * 1024 * 1024 * 4 // 3  # تحويل تقريبي لـ base64
            
            file_logger.log(f"🔍 فحص حجم base64: {len(b64):,} حرف (الحد الأقصى: {max_size_chars:,})")
            
            if len(b64) > max_size_chars:
                raise ValueError(f"الملف كبير جداً ({len(b64):,} حرف). الحد الأقصى: {max_size_chars:,}")
            
            file_logger.log("✅ حجم base64 مقبول")
            
            # تسجيل عينة من base64 للتشخيص
            file_logger.log(f"🔍 بداية base64 (50 حرف): {b64[:50]}")
            file_logger.log(f"🔍 نهاية base64 (50 حرف): {b64[-50:]}")
            
            # فحص سلامة base64
            try:
                file_logger.log("🔍 اختبار فك ترميز base64...")
                test_decode = base64.b64decode(b64)
                file_logger.log(f"✅ base64 صحيح - الحجم المفكوك: {len(test_decode):,} بايت")
            except Exception as decode_error:
                file_logger.log(f"❌ base64 تالف: {decode_error}", "ERROR")
                raise ValueError(f"base64 تالف: {decode_error}")
            
            file_logger.log(f"🔄 إرسال إلى Mistral OCR - الحجم: {len(b64):,} حرف")
            
            # استدعاء Mistral OCR مع معالجة أفضل للأخطاء
            try:
                file_logger.log("📡 بدء استدعاء Mistral OCR API...")
                response = client.ocr.process(
                    model="mistral-ocr-latest",
                    document={
                        "type": "document_url",
                        "document_url": f"data:application/pdf;base64,{b64}"
                    },
                    include_image_base64=False
                )
                file_logger.log("✅ تم استلام الرد من Mistral OCR بنجاح")
                
            except Exception as ocr_error:
                # تسجيل تفاصيل الخطأ
                error_msg = str(ocr_error)
                file_logger.log(f"❌ خطأ في Mistral OCR API: {error_msg}", "ERROR")
                
                # معالجة خاصة لأخطاء OCR
                if "422" in error_msg and "base64" in error_msg:
                    file_logger.log("🔍 الخطأ: مشكلة في تنسيق base64", "ERROR")
                    raise RuntimeError(f"خطأ في تنسيق base64: تأكد من سلامة الملف وحجمه")
                elif "422" in error_msg:
                    file_logger.log("🔍 الخطأ: رفض الطلب من API", "ERROR")
                    raise RuntimeError(f"خطأ في طلب Mistral API: {error_msg}")
                else:
                    file_logger.log("🔍 الخطأ: خطأ عام في معالجة OCR", "ERROR")
                    raise RuntimeError(f"خطأ في معالجة OCR: {error_msg}")
            
            # حفظ محتوى كل صفحة
            file_logger.log(f"📄 معالجة {len(response.pages)} صفحة...")
            full_text = ""
            pages_data = []
            
            for page in response.pages:
                page_content = page.markdown
                full_text += page_content + "\n\n"
                
                file_logger.log(f"📄 حفظ الصفحة {page.index + 1} - طول المحتوى: {len(page_content)} حرف")
                
                # حفظ محتوى الصفحة محلياً
                json_storage.save_document_content(
                    document_id=document_id,
                    page_number=page.index + 1,
                    raw_markdown=page_content
                )
                
                # إضافة بيانات الصفحة للوثيقة الشاملة
                pages_data.append({
                    "page_number": page.index + 1,
                    "content": page_content,
                    "length": len(page_content)
                })
            
            file_logger.log(f"✅ تم حفظ جميع الصفحات - إجمالي النص: {len(full_text)} حرف")
            
            # فهرسة النص
            file_logger.log(f"📚 بدء فهرسة النص للملف: {pdf_filename}")
            index_data = text_indexer.create_full_index(full_text, document_id)
            
            file_logger.log(f"🔍 إحصائيات الفهرسة:")
            file_logger.log(f"   📊 إجمالي الكلمات: {index_data['statistics']['total_words']}")
            file_logger.log(f"   🔤 كلمات فريدة: {index_data['statistics']['unique_words']}")
            file_logger.log(f"   📑 عدد الأجزاء: {len(index_data['chunks'])}")
            
            # حفظ الفهارس محلياً
            file_logger.log("💾 حفظ الفهارس محلياً...")
            for chunk in index_data['chunks']:
                json_storage.create_document_index(
                    document_id=document_id,
                    content_chunk=chunk['content'],
                    keywords=chunk['keywords'],
                    chunk_position=chunk['position']
                )
            
            file_logger.log("✅ تم حفظ جميع الفهارس")
            
            # إنشاء الوثيقة الشاملة
            complete_document = {
                "pages": pages_data,
                "full_text": full_text,
                "index_data": index_data,
                "statistics": {
                    "total_pages": len(response.pages),
                    "total_chars": len(full_text),
                    "total_words": index_data['statistics']['total_words'],
                    "unique_words": index_data['statistics']['unique_words'],
                    "chunks_count": len(index_data['chunks']),
                    "processed_at": datetime.now().isoformat()
                }
            }
            
            # حفظ الوثيقة الشاملة
            file_logger.log("💾 حفظ الوثيقة الشاملة في JSON...")
            json_storage.save_complete_document(document_id, pdf_filename, complete_document)
            
            # تحديث حالة الوثيقة إلى مكتملة
            file_logger.log("🔄 تحديث حالة الوثيقة إلى مكتملة...")
            json_storage.update_document_status(document_id, 'completed')
            file_logger.log("✅ تم تحديث حالة الوثيقة بنجاح")
            
            print(f"✅ تم معالجة {pdf_filename} بنجاح وحفظه في JSON")
            print(f"   📊 عدد الصفحات: {len(response.pages)}")
            print(f"   🔤 عدد الكلمات: {index_data['statistics']['total_words']}")
            print(f"   📑 عدد الأجزاء المفهرسة: {len(index_data['chunks'])}")
            print(f"   💾 البيانات محفوظة محلياً في: json_data/")
            
            return document_id
            
        except Exception as e:
            # تسجيل تفاصيل الفشل
            file_logger.log(f"💥 فشل في معالجة {pdf_filename}: {str(e)}", "ERROR")
            
            # تحديث حالة الوثيقة إلى فشل مع تفاصيل الخطأ
            error_details = {
                'error_message': str(e),
                'error_type': type(e).__name__,
                'processing_stage': 'ocr_processing',
                'timestamp': datetime.now().isoformat()
            }
            
            file_logger.log("🔄 حفظ تفاصيل الخطأ محلياً...")
            
            # تحديث حالة الوثيقة مع تفاصيل الخطأ
            try:
                json_storage.update_document_status(document_id, 'failed')
                
                # حفظ تفاصيل الخطأ في ملف منفصل
                error_file = json_storage.base_dir / f"{document_id}_error.json"
                with open(error_file, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(error_details, f, ensure_ascii=False, indent=2)
                
                file_logger.log("✅ تم حفظ تفاصيل الخطأ محلياً")
            except Exception as storage_error:
                file_logger.log(f"❌ فشل في حفظ تفاصيل الخطأ: {storage_error}", "ERROR")
            
            logging.error(f"فشل في معالجة {pdf_filename}: {e}")
            
            # إعادة رفع الخطأ مع رسالة واضحة
            if "base64" in str(e).lower():
                file_logger.log("🔍 تشخيص: مشكلة في ترميز base64", "ERROR")
                raise RuntimeError(f"مشكلة في ترميز الملف: {str(e)}")
            elif "422" in str(e):
                file_logger.log("🔍 تشخيص: رفض API للطلب (422)", "ERROR")
                raise RuntimeError(f"رفض API للطلب: {str(e)}")
            else:
                file_logger.log("🔍 تشخيص: خطأ عام في المعالجة", "ERROR")
                raise
    
    # تم إزالة دالة save_markdown_file - لا نحتاجها عند التخزين في JSON
    
    def get_processing_statistics(self):
        """الحصول على إحصائيات المعالجة"""
        return json_storage.get_processing_statistics()
    
    def process_all_pdfs(self):
        """معالجة جميع ملفات PDF"""
        pdf_files = self.get_pdf_files()
        
        if not pdf_files:
            print("⚠️ لم يتم العثور على ملفات PDF في المجلد")
            return
        
        print(f"📁 تم العثور على {len(pdf_files)} ملف PDF")
        
        # الحصول على الإحصائيات الحالية
        initial_stats = self.get_processing_statistics()
        print(f"📊 الحالة الحالية:")
        print(f"   ✅ مكتمل: {initial_stats['completed']}")
        print(f"   🔄 قيد المعالجة: {initial_stats['processing']}")
        print(f"   ❌ فشل: {initial_stats['failed']}")
        print(f"   📤 مرفوع: {initial_stats['uploaded']}")
        
        # تصفية الملفات المكتملة
        completed_files = set()
        for doc in json_storage.get_all_documents('completed'):
            completed_files.add(doc['filename'])
        
        to_process = [f for f in pdf_files if f not in completed_files]
        
        if not to_process:
            print("✅ جميع الملفات تم معالجتها مسبقاً")
            return
        
        print(f"🎯 سيتم معالجة {len(to_process)} ملف")
        print("-" * 50)
        
        processed_count = 0
        
        # استخدام شريط التقدم
        with tqdm(to_process, desc="معالجة الملفات", unit="ملف") as pbar:
            for idx, pdf_file in enumerate(pbar, 1):
                pbar.set_description(f"معالجة: {pdf_file[:30]}...")
                
                attempts = 0
                backoff = INITIAL_BACKOFF
                success = False
                
                while attempts < MAX_RETRIES and not success:
                    attempts += 1
                    try:
                        document_id = self.process_pdf_with_ocr(pdf_file)
                        success = True
                        processed_count += 1
                        
                        # تحديث شريط التقدم
                        pbar.set_postfix({
                            'نجح': processed_count,
                            'معرف': document_id[:8] if document_id else 'N/A'
                        })
                        
                        # انتظار قبل الملف التالي
                        if idx < len(to_process):
                            time.sleep(3)
                            
                    except Exception as e:
                        error_msg = str(e)
                        logging.error(f"{pdf_file} المحاولة {attempts} فشلت: {error_msg}")
                        pbar.write(f"❌ خطأ في معالجة {pdf_file} (المحاولة {attempts}): {error_msg}")
                        
                        if attempts < MAX_RETRIES:
                            pbar.write(f"🔄 إعادة المحاولة خلال {backoff} ثانية...")
                            time.sleep(backoff)
                            backoff *= 2
            
            if not success:
                print(f"💥 فشل نهائي: {pdf_file} بعد {attempts} محاولات")
        
        # إحصائيات نهائية
        final_stats = self.get_processing_statistics()
        print("\n" + "=" * 50)
        print("📊 تقرير المعالجة النهائي:")
        print(f"   ✅ تم معالجة بنجاح: {processed_count} من {len(to_process)}")
        print(f"   📈 إجمالي الملفات المكتملة: {final_stats['completed']}")
        print(f"   💾 جميع البيانات محفوظة محلياً في JSON")
        print("=" * 50)

def main():
    """الدالة الرئيسية"""
    import argparse
    
    parser = argparse.ArgumentParser(description='معالج PDF محسن مع التخزين المحلي')
    parser.add_argument('--single-file', type=str, 
                       help='معالجة ملف واحد فقط')
    parser.add_argument('--status', action='store_true',
                       help='عرض إحصائيات المعالجة فقط')
    
    args = parser.parse_args()
    
    print("🚀 بدء معالج PDF المحسن مع التخزين المحلي")
    print("=" * 50)
    
    # إنشاء المعالج
    processor = EnhancedPDFProcessor()
    
    if args.status:
        # عرض الإحصائيات فقط
        stats = processor.get_processing_statistics()
        print("\n📊 إحصائيات المعالجة:")
        print(f"   📄 إجمالي الوثائق: {stats['total']}")
        print(f"   ✅ مكتمل: {stats['completed']}")
        print(f"   🔄 قيد المعالجة: {stats['processing']}")
        print(f"   ❌ فشل: {stats['failed']}")
        print(f"   📤 مرفوع: {stats['uploaded']}")
        return
    
    if args.single_file:
        # معالجة ملف واحد
        try:
            document_id = processor.process_pdf_with_ocr(args.single_file)
            print(f"\n✅ تم معالجة الملف بنجاح")
            print(f"🆔 معرف الوثيقة: {document_id}")
            
            # عرض معلومات الوثيقة
            complete_file = json_storage.base_dir / f"{args.single_file.replace('.pdf', '_complete.json')}"
            if complete_file.exists():
                print(f"\n📋 معلومات الوثيقة:")
                print(f"   📊 الحالة: مكتملة")
                print(f"   💾 ملف البيانات: {complete_file}")
            else:
                print(f"\n⚠️ لم يتم العثور على ملف البيانات الكامل")
        except Exception as e:
            print(f"❌ فشل في معالجة الملف: {e}")
    else:
        # معالجة جميع الملفات
        processor.process_all_pdfs()
    
    print("\n🎉 انتهت المعالجة!")

if __name__ == '__main__':
    main()
