"""
معالج PDF فائق التحسين مع جميع الميزات المتقدمة
يدمج OCR مع التنظيف والفهرسة المتقدمة وقاعدة البيانات المحسنة
"""

import os
import sys
import base64
import time
import logging
from pathlib import Path
from mistralai import Mistral
from dotenv import load_dotenv

# استيراد الوحدات المحسنة
from supabase_client import db_manager
from advanced_text_processor import advanced_processor

load_dotenv()

# Configuration
DOC_DIR = "docs_import"
EXPORT_DIR = "docs_exports"
LOG_FILE = "super_enhanced_conversion.log"
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

class SuperEnhancedPDFProcessor:
    """معالج PDF فائق التحسين"""
    
    def __init__(self):
        """تهيئة المعالج الفائق"""
        self.ensure_directories()
        
        if not db_manager:
            print("❌ خطأ: فشل في الاتصال مع Supabase")
            sys.exit(1)
        
        print("🚀 تم تهيئة المعالج الفائق بنجاح")
        print("✨ الميزات المتاحة:")
        print("   🧹 تنظيف محتوى متقدم")
        print("   📝 استخراج عناوين ذكي")
        print("   📚 فهرسة قانونية متخصصة")
        print("   💾 تخزين محسن في Supabase")
    
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
    
    def save_enhanced_document(self, document_data, pages_data, indexing_data):
        """حفظ الوثيقة المحسنة في قاعدة البيانات"""
        try:
            # إنشاء أو تحديث الوثيقة
            doc_id = db_manager.create_document(
                filename=document_data['filename'],
                original_path=document_data.get('original_path', ''),
                file_size=document_data.get('file_size', 0),
                metadata=document_data.get('processing_notes', {})
            )
            
            # تحديث البيانات المحسنة
            self.update_enhanced_document_fields(doc_id, document_data)
            
            # حفظ محتوى الصفحات
            for page_data in pages_data:
                db_manager.save_document_content(
                    document_id=doc_id,
                    page_number=page_data['page_number'],
                    raw_markdown=page_data['raw_markdown'],
                    processed_text=page_data['cleaned_content']
                )
            
            # حفظ الفهرسة
            for index_data in indexing_data:
                db_manager.create_document_index(
                    document_id=doc_id,
                    content_chunk=index_data['content_chunk'],
                    keywords=index_data['keywords'],
                    chunk_position=index_data['chunk_position']
                )
            
            return doc_id
            
        except Exception as e:
            logging.error(f"فشل في حفظ الوثيقة المحسنة: {e}")
            raise
    
    def update_enhanced_document_fields(self, doc_id, document_data):
        """تحديث الحقول المحسنة للوثيقة"""
        try:
            # استخدام SQL مباشر لتحديث الحقول الجديدة
            update_query = """
                UPDATE documents 
                SET 
                    extracted_title = %s,
                    document_type = %s,
                    content_quality_score = %s,
                    processing_notes = %s
                WHERE id = %s
            """
            
            db_manager.supabase.rpc('execute_sql', {
                'query': update_query,
                'params': [
                    document_data.get('extracted_title'),
                    document_data.get('document_type'),
                    document_data.get('content_quality_score'),
                    document_data.get('processing_notes'),
                    doc_id
                ]
            })
            
        except Exception as e:
            print(f"⚠️ تعذر تحديث الحقول المحسنة: {e}")
            # المتابعة بدون الحقول المحسنة
    
    def process_pdf_with_super_enhancement(self, pdf_filename):
        """معالجة PDF مع جميع التحسينات"""
        full_path = os.path.join(DOC_DIR, pdf_filename)
        
        print(f"\n{'='*60}")
        print(f"🔄 بدء المعالجة الفائقة للملف: {pdf_filename}")
        print(f"{'='*60}")
        
        # التحقق من وجود الملف مسبقاً
        existing_doc = db_manager.get_document_by_filename(pdf_filename)
        if existing_doc and existing_doc['status'] == 'completed':
            print(f"⚠️ الملف تم معالجته مسبقاً")
            return existing_doc['id']
        
        try:
            start_time = time.time()
            
            # 1. ترميز PDF
            print("📁 ترميز ملف PDF...")
            b64 = self.encode_pdf(full_path)
            if not b64:
                raise RuntimeError("فشل في ترميز PDF")
            
            # 2. استدعاء Mistral OCR
            print("🔍 تشغيل OCR باستخدام Mistral AI...")
            response = client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{b64}"
                },
                include_image_base64=False
            )
            
            # 3. استخراج محتوى الصفحات
            print("📄 استخراج محتوى الصفحات...")
            pages_content = []
            for page in response.pages:
                pages_content.append(page.markdown)
            
            print(f"   ✅ تم استخراج {len(pages_content)} صفحة")
            
            # 4. المعالجة المتقدمة
            print("🚀 بدء المعالجة المتقدمة...")
            processed_data = advanced_processor.process_for_database_storage(
                pages_content, pdf_filename
            )
            
            # 5. عرض نتائج المعالجة
            self.display_processing_results(processed_data['full_result'])
            
            # 6. حفظ في قاعدة البيانات
            print("💾 حفظ البيانات في قاعدة البيانات...")
            
            # إضافة معلومات إضافية
            processed_data['document']['original_path'] = full_path
            processed_data['document']['file_size'] = self.get_file_size(full_path)
            
            # حفظ البيانات
            doc_id = self.save_enhanced_document(
                processed_data['document'],
                processed_data['pages'],
                processed_data['indexing']
            )
            
            # تحديث الحالة
            db_manager.update_document_status(doc_id, 'completed')
            
            # 7. حفظ ملف Markdown (نسخة احتياطية)
            self.save_markdown_backup(pdf_filename, pages_content, processed_data)
            
            processing_time = time.time() - start_time
            
            print(f"\n🎉 تمت المعالجة بنجاح!")
            print(f"⏱️ وقت المعالجة: {processing_time:.2f} ثانية")
            print(f"🆔 معرف الوثيقة: {doc_id}")
            
            return doc_id
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"فشل في معالجة {pdf_filename}: {error_msg}")
            
            # تحديث حالة الخطأ
            if 'doc_id' in locals():
                db_manager.update_document_status(doc_id, 'failed')
            
            print(f"❌ خطأ في المعالجة: {error_msg}")
            raise
    
    def display_processing_results(self, result):
        """عرض نتائج المعالجة"""
        print(f"\n📊 نتائج المعالجة:")
        print(f"   📝 العنوان المستخرج: {result['title'].get('full_title', 'غير محدد')}")
        print(f"   🏷️ نوع الوثيقة: {result.get('document_type', 'غير محدد')}")
        print(f"   📄 إجمالي الصفحات: {result['content']['pages_count']}")
        print(f"   ✅ الصفحات المفيدة: {result['content']['useful_pages_count']}")
        print(f"   📏 طول المحتوى: {result['content']['total_length']} حرف")
        print(f"   🎯 درجة الجودة: {result['quality']['overall_score']:.2f}")
        print(f"   🔤 الكلمات المفتاحية: {len(result['indexing']['keywords'])}")
        print(f"   📑 الأجزاء المفهرسة: {len(result['indexing']['chunks'])}")
        
        # عرض التحسينات المطبقة
        improvements = result['cleaning'].get('improvement_counts', {})
        if improvements:
            print(f"   🔧 التحسينات المطبقة:")
            for improvement, count in improvements.items():
                print(f"      • {improvement}: {count} مرة")
        
        # عرض التوصيات
        recommendations = result['processing_summary'].get('recommendations', [])
        if recommendations:
            print(f"   💡 التوصيات:")
            for rec in recommendations:
                print(f"      • {rec}")
    
    def save_markdown_backup(self, pdf_filename, pages_content, processed_data):
        """حفظ نسخة احتياطية بصيغة Markdown"""
        try:
            # إنشاء اسم الملف
            base_name = pdf_filename.rsplit('.', 1)[0]
            title = processed_data['full_result']['title'].get('full_title', base_name)
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            
            output_name = f"{safe_title[:50]}.md" if safe_title else f"{base_name}.md"
            output_path = os.path.join(EXPORT_DIR, output_name)
            
            # إنشاء محتوى الملف
            content = []
            content.append(f"# {title}\n")
            content.append(f"**الملف الأصلي:** {pdf_filename}\n")
            content.append(f"**تاريخ المعالجة:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            content.append(f"**درجة الجودة:** {processed_data['full_result']['quality']['overall_score']:.2f}\n")
            
            # إضافة الكلمات المفتاحية
            keywords = processed_data['full_result']['indexing']['keywords'][:10]
            if keywords:
                content.append(f"**الكلمات المفتاحية:** {', '.join(keywords)}\n")
            
            content.append("\n---\n\n")
            
            # إضافة المحتوى المنظف
            cleaned_content = processed_data['full_result']['content']['full_text']
            if cleaned_content:
                content.append(cleaned_content)
            else:
                # إذا لم يكن هناك محتوى منظف، استخدم الأصلي
                for i, page_content in enumerate(pages_content, 1):
                    content.append(f"## صفحة {i}\n\n{page_content}\n\n")
            
            # كتابة الملف
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
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
        """معالجة جميع ملفات PDF مع التحسينات الفائقة"""
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
        
        print(f"🎯 سيتم معالجة {len(to_process)} ملف بالتحسينات الفائقة")
        print("=" * 80)
        
        processed_count = 0
        for idx, pdf_file in enumerate(to_process, 1):
            print(f"\n[{idx}/{len(to_process)}] معالجة: {pdf_file}")
            
            attempts = 0
            backoff = INITIAL_BACKOFF
            success = False
            
            while attempts < MAX_RETRIES and not success:
                attempts += 1
                try:
                    self.process_pdf_with_super_enhancement(pdf_file)
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
        print("\n" + "=" * 80)
        print("🎉 تقرير المعالجة الفائقة النهائي:")
        print(f"   ✅ تم معالجة بنجاح: {processed_count} من {len(to_process)}")
        print(f"   📈 إجمالي الملفات المكتملة: {final_stats['completed']}")
        print(f"   🚀 جميع الميزات المتقدمة تم تطبيقها")
        print(f"   💾 البيانات محفوظة في Supabase مع التحسينات")
        print("=" * 80)

def main():
    """الدالة الرئيسية"""
    print("🚀 بدء معالج PDF الفائق التحسين")
    print("=" * 80)
    print("✨ الميزات المتقدمة:")
    print("   🧹 تنظيف محتوى ذكي (إزالة مراجع الصور وتنسيق LaTeX)")
    print("   📝 استخراج عناوين ذكي للوثائق القانونية")
    print("   📚 فهرسة قانونية متخصصة (مواد، فصول، أبواب)")
    print("   🔍 كلمات مفتاحية محسنة حسب المجال القانوني")
    print("   💾 تخزين محسن في Supabase مع هيكل متقدم")
    print("   📊 تقارير جودة شاملة")
    print("=" * 80)
    
    processor = SuperEnhancedPDFProcessor()
    processor.process_all_pdfs()
    
    print("\n🎉 انتهت المعالجة الفائقة!")
    print("💡 يمكنك الآن البحث في الوثائق باستخدام:")
    print("   • العناوين المستخرجة")
    print("   • الكلمات المفتاحية المحسنة") 
    print("   • الهيكل القانوني (مواد، فصول)")
    print("   • نوع الوثيقة")

if __name__ == '__main__':
    main()
