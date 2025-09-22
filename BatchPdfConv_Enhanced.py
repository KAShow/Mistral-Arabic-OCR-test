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
    """معالج PDF محسن مع دعم Supabase"""
    
    def __init__(self):
        """تهيئة المعالج"""
        self.ensure_directories()
        
        # التحقق من الاتصال بقاعدة البيانات
        if not db_manager:
            print("❌ خطأ: فشل في الاتصال مع Supabase")
            sys.exit(1)
        
        print("✅ تم تهيئة المعالج بنجاح")
    
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
        """ترميز ملف PDF إلى base64"""
        try:
            with open(pdf_path, "rb") as pdf_file:
                return base64.b64encode(pdf_file.read()).decode('utf-8')
        except Exception as e:
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
        """معالجة PDF باستخدام OCR وحفظ النتائج في Supabase"""
        full_path = os.path.join(DOC_DIR, pdf_filename)
        
        # التحقق من وجود الملف في قاعدة البيانات
        existing_doc = db_manager.get_document_by_filename(pdf_filename)
        if existing_doc and existing_doc['status'] == 'completed':
            print(f"⚠️ الملف {pdf_filename} تم معالجته مسبقاً")
            return existing_doc['id']
        
        # إنشاء سجل جديد أو تحديث الموجود
        file_size = self.get_file_size(full_path)
        
        if existing_doc:
            document_id = existing_doc['id']
            db_manager.update_document_status(document_id, 'processing')
        else:
            document_id = db_manager.create_document(
                filename=pdf_filename,
                original_path=full_path,
                file_size=file_size,
                metadata={'processor': 'mistral-ocr-latest'}
            )
            db_manager.update_document_status(document_id, 'processing')
        
        try:
            # ترميز PDF
            b64 = self.encode_pdf(full_path)
            if not b64:
                raise RuntimeError("فشل في ترميز PDF")
            
            print(f"🔄 معالجة OCR للملف: {pdf_filename}")
            
            # استدعاء Mistral OCR
            response = client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{b64}"
                },
                include_image_base64=False
            )
            
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
            
            print(f"✅ تم معالجة {pdf_filename} بنجاح")
            print(f"   📊 عدد الصفحات: {len(response.pages)}")
            print(f"   🔤 عدد الكلمات: {index_data['statistics']['total_words']}")
            print(f"   📑 عدد الأجزاء المفهرسة: {len(index_data['chunks'])}")
            
            return document_id
            
        except Exception as e:
            # تحديث حالة الوثيقة إلى فشل
            db_manager.update_document_status(document_id, 'failed')
            logging.error(f"فشل في معالجة {pdf_filename}: {e}")
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
        for idx, pdf_file in enumerate(to_process, 1):
            print(f"\n[{idx}/{len(to_process)}] معالجة: {pdf_file}")
            
            attempts = 0
            backoff = INITIAL_BACKOFF
            success = False
            
            while attempts < MAX_RETRIES and not success:
                attempts += 1
                try:
                    self.process_pdf_with_ocr(pdf_file)
                    success = True
                    processed_count += 1
                    
                    # انتظار قبل الملف التالي
                    if idx < len(to_process):
                        print("⏳ انتظار 3 ثوانٍ قبل الملف التالي...")
                        time.sleep(3)
                        
                except Exception as e:
                    error_msg = str(e)
                    logging.error(f"{pdf_file} المحاولة {attempts} فشلت: {error_msg}")
                    print(f"❌ خطأ في معالجة {pdf_file} (المحاولة {attempts}): {error_msg}")
                    
                    if attempts < MAX_RETRIES:
                        print(f"🔄 إعادة المحاولة خلال {backoff} ثانية...")
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
    print("🚀 بدء معالج PDF المحسن مع Supabase")
    print("=" * 50)
    
    processor = EnhancedPDFProcessor()
    processor.process_all_pdfs()
    
    print("\n🎉 انتهت المعالجة!")

if __name__ == '__main__':
    main()
