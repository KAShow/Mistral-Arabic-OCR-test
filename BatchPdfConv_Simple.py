"""
معالج PDF مبسط مع التحسينات الأساسية
يستخدم قاعدة البيانات الأصلية مع تحسينات المحتوى والعناوين
"""

import os
import sys
import base64
import time
import logging
from pathlib import Path
from mistralai import Mistral
from dotenv import load_dotenv

# استيراد المكونات الأساسية فقط
from supabase_client import db_manager
from content_cleaner import content_cleaner
from title_extractor import title_extractor

load_dotenv()

# Configuration
DOC_DIR = "docs_import"
EXPORT_DIR = "docs_exports"
LOG_FILE = "simple_conversion.log"
MAX_RETRIES = 5
INITIAL_BACKOFF = 1

# Initialize logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
)

# Ensure API key is set
API_KEY = os.getenv("MISTRAL_API_KEY")
if not API_KEY:
    API_KEY = "97ZQlsV45YrDusgZRwjArWGbh3nerFPb"
    print("⚠️ استخدام مفتاح Mistral API الاحتياطي المدمج")

client = Mistral(api_key=API_KEY)

class SimplePDFProcessor:
    """معالج PDF مبسط مع التحسينات الأساسية"""
    
    def __init__(self):
        """تهيئة المعالج المبسط"""
        self.ensure_directories()
        
        if not db_manager:
            print("❌ خطأ: فشل في الاتصال مع Supabase")
            sys.exit(1)
        
        print("✅ تم تهيئة المعالج المبسط بنجاح")
        print("🔧 الميزات المتاحة:")
        print("   🧹 تنظيف المحتوى (إزالة مراجع الصور)")
        print("   📝 استخراج العناوين الذكي")
        print("   📚 فهرسة أساسية محسنة")
        print("   💾 تخزين في قاعدة البيانات الأصلية")
    
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
    
    def update_document_with_extracted_info(self, doc_id, extracted_title, document_type):
        """تحديث الوثيقة بالمعلومات المستخرجة"""
        try:
            # استخدام طريقة آمنة للتحديث
            result = db_manager.supabase.table("documents").update({
                "extracted_title": extracted_title,
                "document_type": document_type
            }).eq("id", doc_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"⚠️ تعذر تحديث المعلومات المستخرجة: {e}")
            # المتابعة بدون التحديث
            return False
    
    def create_enhanced_keywords(self, text):
        """إنشاء كلمات مفتاحية محسنة"""
        # تنظيف النص أولاً
        cleaned_result = content_cleaner.clean_content(text)
        if not cleaned_result['is_useful']:
            return []
        
        # استخراج كلمات أساسية محسنة
        import re
        from collections import Counter
        
        # كلمات الوقف العربية
        stop_words = {
            'في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك',
            'التي', 'الذي', 'أن', 'إن', 'كان', 'كانت', 'يكون', 'تكون',
            'ما', 'لا', 'ليس', 'غير', 'بل', 'لكن', 'أو', 'كل', 'بعض',
            'هو', 'هي', 'هم', 'هن', 'أنت', 'أنا', 'نحن'
        }
        
        # استخراج الكلمات العربية
        words = re.findall(r'[\u0600-\u06FF]+', cleaned_result['cleaned_text'])
        
        # تصفية الكلمات
        filtered_words = [
            word for word in words 
            if len(word) > 2 and word.lower() not in stop_words
        ]
        
        # حساب التكرار والحصول على أهم 20 كلمة
        word_freq = Counter(filtered_words)
        top_words = [word for word, freq in word_freq.most_common(20)]
        
        return top_words
    
    def process_pdf_simple(self, pdf_filename):
        """معالجة PDF بالطريقة المبسطة"""
        full_path = os.path.join(DOC_DIR, pdf_filename)
        
        print(f"\n{'='*50}")
        print(f"🔄 معالجة مبسطة للملف: {pdf_filename}")
        print(f"{'='*50}")
        
        # التحقق من وجود الملف مسبقاً
        existing_doc = db_manager.get_document_by_filename(pdf_filename)
        if existing_doc and existing_doc['status'] == 'completed':
            print(f"⚠️ الملف تم معالجته مسبقاً")
            return existing_doc['id']
        
        try:
            start_time = time.time()
            
            # 1. إنشاء أو تحديث سجل الوثيقة
            file_size = self.get_file_size(full_path)
            
            if existing_doc:
                document_id = existing_doc['id']
                db_manager.update_document_status(document_id, 'processing')
            else:
                document_id = db_manager.create_document(
                    filename=pdf_filename,
                    original_path=full_path,
                    file_size=file_size,
                    metadata={'processor': 'simple-enhanced'}
                )
                db_manager.update_document_status(document_id, 'processing')
            
            # 2. ترميز PDF
            print("📁 ترميز ملف PDF...")
            b64 = self.encode_pdf(full_path)
            if not b64:
                raise RuntimeError("فشل في ترميز PDF")
            
            # 3. استدعاء Mistral OCR
            print("🔍 تشغيل OCR باستخدام Mistral AI...")
            response = client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{b64}"
                },
                include_image_base64=False
            )
            
            # 4. معالجة وتنظيف المحتوى
            print("🧹 تنظيف وتحسين المحتوى...")
            pages_content = []
            cleaned_pages = []
            full_text = ""
            
            for page in response.pages:
                page_content = page.markdown
                pages_content.append(page_content)
                
                # تنظيف المحتوى
                cleaned_result = content_cleaner.clean_content(page_content)
                cleaned_pages.append(cleaned_result)
                
                if cleaned_result['is_useful']:
                    full_text += cleaned_result['cleaned_text'] + "\n\n"
            
            print(f"   ✅ تم تنظيف {len(pages_content)} صفحة")
            
            # 5. استخراج العنوان
            print("📝 استخراج العنوان...")
            title_result = title_extractor.extract_title_from_pages(pages_content)
            
            extracted_title = title_result.get('full_title') or pdf_filename
            document_type = title_extractor.extract_document_type(title_result.get('title', ''))
            
            # التأكد من عدم تجاوز 10 كلمات
            title_words = extracted_title.split()
            if len(title_words) > 10:
                extracted_title = ' '.join(title_words[:10]) + "..."
            
            print(f"   📄 العنوان: {extracted_title}")
            print(f"   🏷️ النوع: {document_type}")
            print(f"   📊 عدد كلمات العنوان: {len(extracted_title.split())}")
            
            # 6. حفظ محتوى الصفحات
            print("💾 حفظ محتوى الصفحات...")
            for i, (original_content, cleaned_result) in enumerate(zip(pages_content, cleaned_pages)):
                if cleaned_result['is_useful']:
                    db_manager.save_document_content(
                        document_id=document_id,
                        page_number=i + 1,
                        raw_markdown=original_content,
                        processed_text=cleaned_result['cleaned_text']
                    )
            
            # 7. إنشاء فهرسة محسنة
            print("📚 إنشاء الفهرسة...")
            if full_text:
                keywords = self.create_enhanced_keywords(full_text)
                
                # تقسيم النص إلى أجزاء
                chunks = self.create_simple_chunks(full_text)
                
                for i, chunk in enumerate(chunks):
                    chunk_keywords = self.create_enhanced_keywords(chunk)[:10]
                    db_manager.create_document_index(
                        document_id=document_id,
                        content_chunk=chunk,
                        keywords=chunk_keywords,
                        chunk_position=i
                    )
                
                print(f"   🔤 الكلمات المفتاحية: {len(keywords)}")
                print(f"   📑 الأجزاء المفهرسة: {len(chunks)}")
            
            # 8. تحديث معلومات الوثيقة
            self.update_document_with_extracted_info(document_id, extracted_title, document_type)
            
            # 9. تحديث الحالة
            db_manager.update_document_status(document_id, 'completed')
            
            # 10. حفظ ملف Markdown (نسخة احتياطية)
            self.save_simple_markdown(pdf_filename, pages_content, extracted_title, full_text)
            
            processing_time = time.time() - start_time
            
            print(f"\n🎉 تمت المعالجة المبسطة بنجاح!")
            print(f"⏱️ وقت المعالجة: {processing_time:.2f} ثانية")
            print(f"🆔 معرف الوثيقة: {document_id}")
            
            return document_id
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"فشل في معالجة {pdf_filename}: {error_msg}")
            
            # تحديث حالة الخطأ
            if 'document_id' in locals():
                db_manager.update_document_status(document_id, 'failed')
            
            print(f"❌ خطأ في المعالجة: {error_msg}")
            raise
    
    def create_simple_chunks(self, text, chunk_size=500):
        """تقسيم النص إلى أجزاء بسيطة"""
        if not text:
            return []
        
        # تقسيم بالفقرات أولاً
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            if len(current_chunk + paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph + '\n\n'
            else:
                current_chunk += paragraph + '\n\n'
        
        # إضافة الجزء الأخير
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def save_simple_markdown(self, pdf_filename, pages_content, title, cleaned_text):
        """حفظ نسخة احتياطية مبسطة"""
        try:
            # إنشاء اسم الملف
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            output_name = f"{safe_title[:50]}.md" if safe_title else f"{pdf_filename.rsplit('.', 1)[0]}.md"
            output_path = os.path.join(EXPORT_DIR, output_name)
            
            # إنشاء محتوى الملف
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                f.write(f"**الملف الأصلي:** {pdf_filename}\n")
                f.write(f"**تاريخ المعالجة:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                
                if cleaned_text:
                    f.write(cleaned_text)
                else:
                    # إذا لم يكن هناك نص منظف، استخدم الأصلي
                    for i, page_content in enumerate(pages_content, 1):
                        f.write(f"## صفحة {i}\n\n{page_content}\n\n")
            
            print(f"📄 تم حفظ النسخة الاحتياطية: {output_path}")
            
        except Exception as e:
            print(f"⚠️ تعذر حفظ النسخة الاحتياطية: {e}")
    
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
        """معالجة جميع ملفات PDF بالطريقة المبسطة"""
        pdf_files = self.get_pdf_files()
        
        if not pdf_files:
            print("⚠️ لم يتم العثور على ملفات PDF في المجلد")
            return
        
        print(f"🎯 تم العثور على {len(pdf_files)} ملف PDF")
        
        # الحصول على الإحصائيات الحالية
        initial_stats = self.get_processing_statistics()
        print(f"📊 الحالة الحالية:")
        print(f"   ✅ مكتمل: {initial_stats['completed']}")
        print(f"   🔄 قيد المعالجة: {initial_stats['processing']}")
        print(f"   ❌ فشل: {initial_stats['failed']}")
        
        # تصفية الملفات المكتملة
        completed_files = set()
        for doc in db_manager.get_all_documents('completed'):
            completed_files.add(doc['filename'])
        
        to_process = [f for f in pdf_files if f not in completed_files]
        
        if not to_process:
            print("✅ جميع الملفات تم معالجتها مسبقاً")
            return
        
        print(f"🎯 سيتم معالجة {len(to_process)} ملف بالطريقة المبسطة")
        print("=" * 60)
        
        processed_count = 0
        for idx, pdf_file in enumerate(to_process, 1):
            print(f"\n[{idx}/{len(to_process)}] معالجة: {pdf_file}")
            
            attempts = 0
            backoff = INITIAL_BACKOFF
            success = False
            
            while attempts < MAX_RETRIES and not success:
                attempts += 1
                try:
                    self.process_pdf_simple(pdf_file)
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
        print("\n" + "=" * 60)
        print("🎉 تقرير المعالجة المبسطة النهائي:")
        print(f"   ✅ تم معالجة بنجاح: {processed_count} من {len(to_process)}")
        print(f"   📈 إجمالي الملفات المكتملة: {final_stats['completed']}")
        print(f"   🧹 تم تنظيف المحتوى وإزالة مراجع الصور")
        print(f"   📝 تم استخراج العناوين الحقيقية")
        print(f"   💾 البيانات محفوظة في قاعدة البيانات الأصلية")
        print("=" * 60)

def main():
    """الدالة الرئيسية"""
    print("🚀 بدء معالج PDF المبسط مع التحسينات الأساسية")
    print("=" * 60)
    print("✨ الميزات المتاحة:")
    print("   🧹 تنظيف محتوى ذكي (إزالة مراجع الصور وتنسيق LaTeX)")
    print("   📝 استخراج عناوين ذكي للوثائق القانونية")
    print("   📚 فهرسة أساسية محسنة")
    print("   💾 تخزين في قاعدة البيانات الأصلية (بدون تعقيد)")
    print("   📄 نسخ احتياطية بصيغة Markdown")
    print("=" * 60)
    
    processor = SimplePDFProcessor()
    processor.process_all_pdfs()
    
    print("\n🎉 انتهت المعالجة المبسطة!")
    print("💡 النتائج المحققة:")
    print("   ✅ عناوين حقيقية بدلاً من (img-0.jpeg)")
    print("   ✅ محتوى نظيف بدون مراجع صور")
    print("   ✅ كلمات مفتاحية محسنة")
    print("   ✅ قاعدة بيانات بسيطة وفعالة")

if __name__ == '__main__':
    main()
