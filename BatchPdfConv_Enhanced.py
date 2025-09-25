"""
معالج PDF محسن مع دعم Supabase والفهرسة الذكية
يدمج OCR مع قاعدة البيانات والفهرسة التلقائية
"""

import os
import sys
import base64
import time
import logging
from pathlib import Path
from mistralai import Mistral
from dotenv import load_dotenv
from tqdm import tqdm

# استيراد الوحدات المخصصة
from supabase_client import db_manager
from text_indexer import text_indexer

load_dotenv()

# Configuration
DOC_DIR = "docs_import"
EXPORT_DIR = "docs_exports"
LOG_FILE = "supabase_conversion.log"
MAX_RETRIES = 5
INITIAL_BACKOFF = 1  # in seconds

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
    """معالج PDF محسن مع دعم Supabase ورفع الملفات"""
    
    def __init__(self, enable_upload=True):
        """تهيئة المعالج"""
        self.enable_upload = enable_upload
        self.ensure_directories()
        
        # التحقق من الاتصال بقاعدة البيانات
        if not db_manager:
            print("❌ خطأ: فشل في الاتصال مع Supabase")
            sys.exit(1)
        
        print("✅ تم تهيئة المعالج بنجاح")
        if self.enable_upload:
            print("📤 رفع الملفات إلى Supabase مفعل")
    
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
            with open(pdf_path, "rb") as pdf_file:
                pdf_content = pdf_file.read()
                
            # التحقق من صحة الملف
            if len(pdf_content) == 0:
                raise ValueError("الملف فارغ")
                
            if not pdf_content.startswith(b'%PDF'):
                raise ValueError("الملف ليس PDF صالح")
            
            # ترميز base64
            encoded = base64.b64encode(pdf_content).decode('utf-8')
            
            # التحقق من صحة base64
            if not encoded or len(encoded) < 100:
                raise ValueError("فشل في ترميز base64 بشكل صحيح")
            
            # اختبار فك الترميز للتأكد
            try:
                decoded_test = base64.b64decode(encoded)
                if len(decoded_test) != len(pdf_content):
                    raise ValueError("base64 لا يطابق الملف الأصلي")
            except Exception:
                raise ValueError("base64 تالف - فشل في فك الترميز")
            
            print(f"📏 حجم الملف: {len(pdf_content):,} بايت")
            print(f"📝 طول base64: {len(encoded):,} حرف")
            print(f"✅ تم ترميز PDF بنجاح")
            
            return encoded
            
        except Exception as e:
            logging.error(f"فشل في ترميز {pdf_path}: {e}")
            print(f"❌ خطأ في ترميز الملف: {e}")
            return None
    
    def get_file_size(self, file_path):
        """الحصول على حجم الملف"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logging.error(f"فشل في الحصول على حجم الملف {file_path}: {e}")
            return 0
    
    def process_pdf_with_ocr(self, pdf_filename):
        """معالجة PDF باستخدام OCR وحفظ النتائج في Supabase مع رفع الملف"""
        full_path = os.path.join(DOC_DIR, pdf_filename)
        
        # التحقق من وجود الملف في قاعدة البيانات
        existing_doc = db_manager.get_document_by_filename(pdf_filename)
        if existing_doc and existing_doc['status'] == 'completed':
            print(f"⚠️ الملف {pdf_filename} تم معالجته مسبقاً")
            return existing_doc['id']
        
        # رفع الملف إلى Supabase Storage إذا كان مفعلاً
        if self.enable_upload and not existing_doc:
            try:
                print(f"📤 رفع الملف إلى Supabase Storage: {pdf_filename}")
                document_id = db_manager.upload_pdf_file(full_path, pdf_filename)
                print(f"✅ تم رفع الملف بنجاح - معرف الوثيقة: {document_id}")
            except Exception as e:
                print(f"⚠️ فشل رفع الملف، سيتم المتابعة بالمعالجة المحلية: {e}")
                # إنشاء سجل محلي إذا فشل الرفع
                file_size = self.get_file_size(full_path)
                document_id = db_manager.create_document(
                    filename=pdf_filename,
                    original_path=full_path,
                    file_size=file_size,
                    metadata={'processor': 'mistral-ocr-latest', 'upload_failed': True}
                )
        elif existing_doc:
            document_id = existing_doc['id']
            db_manager.update_document_status(document_id, 'processing')
        else:
            # إنشاء سجل محلي إذا كان الرفع غير مفعل
            file_size = self.get_file_size(full_path)
            document_id = db_manager.create_document(
                filename=pdf_filename,
                original_path=full_path,
                file_size=file_size,
                metadata={'processor': 'mistral-ocr-latest', 'local_only': True}
            )
            db_manager.update_document_status(document_id, 'processing')
        
        try:
            # ترميز PDF
            b64 = self.encode_pdf(full_path)
            if not b64:
                raise RuntimeError("فشل في ترميز PDF")
            
            print(f"🔄 معالجة OCR للملف: {pdf_filename}")
            
            # التحقق من حجم base64 قبل الإرسال
            max_size_mb = 50  # حد أقصى 50 ميجا
            max_size_chars = max_size_mb * 1024 * 1024 * 4 // 3  # تحويل تقريبي لـ base64
            
            if len(b64) > max_size_chars:
                raise ValueError(f"الملف كبير جداً ({len(b64):,} حرف). الحد الأقصى: {max_size_chars:,}")
            
            print(f"🔄 إرسال إلى Mistral OCR - الحجم: {len(b64):,} حرف")
            
            # استدعاء Mistral OCR مع معالجة أفضل للأخطاء
            try:
                response = client.ocr.process(
                    model="mistral-ocr-latest",
                    document={
                        "type": "document_url",
                        "document_url": f"data:application/pdf;base64,{b64}"
                    },
                    include_image_base64=False
                )
            except Exception as ocr_error:
                # معالجة خاصة لأخطاء OCR
                error_msg = str(ocr_error)
                if "422" in error_msg and "base64" in error_msg:
                    raise RuntimeError(f"خطأ في تنسيق base64: تأكد من سلامة الملف وحجمه")
                elif "422" in error_msg:
                    raise RuntimeError(f"خطأ في طلب Mistral API: {error_msg}")
                else:
                    raise RuntimeError(f"خطأ في معالجة OCR: {error_msg}")
            
            # حفظ محتوى كل صفحة
            full_text = ""
            for page in response.pages:
                page_content = page.markdown
                full_text += page_content + "\n\n"
                
                # حفظ محتوى الصفحة في قاعدة البيانات
                db_manager.save_document_content(
                    document_id=document_id,
                    page_number=page.index + 1,
                    raw_markdown=page_content
                )
            
            # إنشاء ملف Markdown (للنسخ الاحتياطي)
            self.save_markdown_file(pdf_filename, response.pages)
            
            # فهرسة النص
            print(f"📚 فهرسة النص للملف: {pdf_filename}")
            index_data = text_indexer.create_full_index(full_text, document_id)
            
            # حفظ الفهارس في قاعدة البيانات
            for chunk in index_data['chunks']:
                db_manager.create_document_index(
                    document_id=document_id,
                    content_chunk=chunk['content'],
                    keywords=chunk['keywords'],
                    chunk_position=chunk['position']
                )
            
            # تحديث حالة الوثيقة إلى مكتملة
            db_manager.update_document_status(document_id, 'completed')
            
            # استدعاء Edge Function للمعالجة الإضافية إذا كان الرفع مفعلاً
            if self.enable_upload:
                try:
                    print(f"🔄 استدعاء Edge Function للمعالجة الإضافية...")
                    success = db_manager.trigger_processing(document_id, full_path, pdf_filename)
                    if success:
                        print(f"✅ تم استدعاء Edge Function بنجاح")
                    else:
                        print(f"⚠️ فشل في استدعاء Edge Function، لكن المعالجة المحلية اكتملت")
                except Exception as e:
                    print(f"⚠️ خطأ في استدعاء Edge Function: {e}")
            
            print(f"✅ تم معالجة {pdf_filename} بنجاح")
            print(f"   📊 عدد الصفحات: {len(response.pages)}")
            print(f"   🔤 عدد الكلمات: {index_data['statistics']['total_words']}")
            print(f"   📑 عدد الأجزاء المفهرسة: {len(index_data['chunks'])}")
            
            return document_id
            
        except Exception as e:
            # تحديث حالة الوثيقة إلى فشل مع تفاصيل الخطأ
            error_details = {
                'error_message': str(e),
                'error_type': type(e).__name__,
                'processing_stage': 'ocr_processing'
            }
            
            # حفظ تفاصيل الخطأ في metadata
            try:
                result = db_manager.supabase.table("documents").update({
                    "status": "failed",
                    "metadata": error_details
                }).eq("id", document_id).execute()
            except:
                # إذا فشل في تحديث metadata، استخدم الطريقة البسيطة
                db_manager.update_document_status(document_id, 'failed')
            
            logging.error(f"فشل في معالجة {pdf_filename}: {e}")
            print(f"💥 فشل في معالجة {pdf_filename}: {str(e)}")
            
            # إعادة رفع الخطأ مع رسالة واضحة
            if "base64" in str(e).lower():
                raise RuntimeError(f"مشكلة في ترميز الملف: {str(e)}")
            elif "422" in str(e):
                raise RuntimeError(f"رفض API للطلب: {str(e)}")
            else:
                raise
    
    def save_markdown_file(self, pdf_filename, pages):
        """حفظ ملف Markdown (نسخة احتياطية)"""
        output_name = pdf_filename.rsplit('.', 1)[0] + '.md'
        output_path = os.path.join(EXPORT_DIR, output_name)
        
        # التأكد من وجود مجلد الإخراج
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(output_path, 'w', encoding='utf-8') as md_file:
            for page in pages:
                md_file.write(f"## صفحة {page.index + 1}\n\n")
                md_file.write(page.markdown + "\n\n")
    
    def get_processing_statistics(self):
        """الحصول على إحصائيات المعالجة"""
        all_docs = db_manager.get_all_documents()
        
        stats = {
            'total': len(all_docs),
            'completed': len([d for d in all_docs if d['status'] == 'completed']),
            'processing': len([d for d in all_docs if d['status'] == 'processing']),
            'failed': len([d for d in all_docs if d['status'] == 'failed']),
            'uploaded': len([d for d in all_docs if d['status'] == 'uploaded'])
        }
        
        return stats
    
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
        for doc in db_manager.get_all_documents('completed'):
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
        print(f"   💾 جميع البيانات محفوظة في Supabase")
        print("=" * 50)

def main():
    """الدالة الرئيسية"""
    import argparse
    
    parser = argparse.ArgumentParser(description='معالج PDF محسن مع دعم Supabase')
    parser.add_argument('--no-upload', action='store_true', 
                       help='تعطيل رفع الملفات إلى Supabase Storage')
    parser.add_argument('--single-file', type=str, 
                       help='معالجة ملف واحد فقط')
    parser.add_argument('--status', action='store_true',
                       help='عرض إحصائيات المعالجة فقط')
    
    args = parser.parse_args()
    
    print("🚀 بدء معالج PDF المحسن مع Supabase")
    print("=" * 50)
    
    # إنشاء المعالج
    processor = EnhancedPDFProcessor(enable_upload=not args.no_upload)
    
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
            if processor.enable_upload:
                info = db_manager.get_processed_document_info(document_id)
                if info:
                    print(f"\n📋 معلومات الوثيقة:")
                    print(f"   📊 الحالة: {info['statistics']['status']}")
                    print(f"   📑 عدد الصفحات: {info['statistics']['total_pages']}")
                    print(f"   🔍 عدد الفهارس: {info['statistics']['total_indexes']}")
        except Exception as e:
            print(f"❌ فشل في معالجة الملف: {e}")
    else:
        # معالجة جميع الملفات
        processor.process_all_pdfs()
    
    print("\n🎉 انتهت المعالجة!")

if __name__ == '__main__':
    main()
