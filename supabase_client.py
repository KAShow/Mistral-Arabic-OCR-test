"""
عميل Supabase للتفاعل مع قاعدة البيانات
يدير العمليات الأساسية للوثائق والمحتوى والفهرسة
"""

import os
import json
import uuid
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

class SupabaseManager:
    """مدير قاعدة البيانات Supabase"""
    
    def __init__(self):
        """تهيئة الاتصال مع Supabase"""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        # إعدادات احتياطية مدمجة
        if not self.url or not self.key:
            self.url = "https://fdnruljygqbpidrspyyl.supabase.co"
            self.key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZkbnJ1bGp5Z3FicGlkcnNweXlsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1ODU2MzIsImV4cCI6MjA3MzE2MTYzMn0.ZPbraTaW7InlPCiuD8kIsi7ZogSqzbmj1iw3vXAmxHQ"
            print("⚠️ استخدام الإعدادات الاحتياطية المدمجة لـ Supabase")
        
        if not self.url or not self.key:
            raise ValueError("يجب تعيين SUPABASE_URL و SUPABASE_KEY في متغيرات البيئة")
        
        self.supabase: Client = create_client(self.url, self.key)
    
    def create_document(self, filename: str, original_path: str, file_size: int, metadata: Dict = None) -> str:
        """
        إنشاء سجل وثيقة جديدة
        
        Args:
            filename: اسم الملف
            original_path: المسار الأصلي للملف
            file_size: حجم الملف بالبايت
            metadata: بيانات إضافية (اختيارية)
        
        Returns:
            معرف الوثيقة الجديدة
        """
        try:
            document_data = {
                "filename": filename,
                "original_path": original_path,
                "file_size": file_size,
                "status": "uploaded",
                "metadata": metadata or {}
            }
            
            result = self.supabase.table("documents").insert(document_data).execute()
            
            if result.data:
                return result.data[0]["id"]
            else:
                raise Exception("فشل في إنشاء سجل الوثيقة")
                
        except Exception as e:
            print(f"خطأ في إنشاء الوثيقة: {e}")
            raise
    
    def update_document_status(self, document_id: str, status: str) -> bool:
        """
        تحديث حالة الوثيقة
        
        Args:
            document_id: معرف الوثيقة
            status: الحالة الجديدة (uploaded, processing, completed, failed)
        
        Returns:
            True إذا تم التحديث بنجاح
        """
        try:
            result = self.supabase.table("documents").update({
                "status": status
            }).eq("id", document_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"خطأ في تحديث حالة الوثيقة: {e}")
            return False
    
    def save_document_content(self, document_id: str, page_number: int, raw_markdown: str, processed_text: str = None) -> str:
        """
        حفظ محتوى صفحة من الوثيقة
        
        Args:
            document_id: معرف الوثيقة
            page_number: رقم الصفحة
            raw_markdown: المحتوى الخام بصيغة Markdown
            processed_text: النص المعالج (اختياري)
        
        Returns:
            معرف سجل المحتوى
        """
        try:
            content_data = {
                "document_id": document_id,
                "page_number": page_number,
                "raw_markdown": raw_markdown,
                "processed_text": processed_text or raw_markdown
            }
            
            result = self.supabase.table("document_content").insert(content_data).execute()
            
            if result.data:
                return result.data[0]["id"]
            else:
                raise Exception("فشل في حفظ محتوى الوثيقة")
                
        except Exception as e:
            print(f"خطأ في حفظ المحتوى: {e}")
            raise
    
    def create_document_index(self, document_id: str, content_chunk: str, keywords: List[str], chunk_position: int = 0) -> str:
        """
        إنشاء فهرس للوثيقة
        
        Args:
            document_id: معرف الوثيقة
            content_chunk: جزء من المحتوى للفهرسة
            keywords: قائمة الكلمات المفتاحية
            chunk_position: موقع الجزء في الوثيقة
        
        Returns:
            معرف سجل الفهرس
        """
        try:
            index_data = {
                "document_id": document_id,
                "content_chunk": content_chunk,
                "keywords": keywords,
                "chunk_position": chunk_position
            }
            
            result = self.supabase.table("document_index").insert(index_data).execute()
            
            if result.data:
                return result.data[0]["id"]
            else:
                raise Exception("فشل في إنشاء فهرس الوثيقة")
                
        except Exception as e:
            print(f"خطأ في إنشاء الفهرس: {e}")
            raise
    
    def get_document_by_filename(self, filename: str) -> Optional[Dict]:
        """
        البحث عن وثيقة باسم الملف
        
        Args:
            filename: اسم الملف
        
        Returns:
            بيانات الوثيقة أو None
        """
        try:
            result = self.supabase.table("documents").select("*").eq("filename", filename).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"خطأ في البحث عن الوثيقة: {e}")
            return None
    
    def get_all_documents(self, status: str = None) -> List[Dict]:
        """
        الحصول على جميع الوثائق أو حسب الحالة
        
        Args:
            status: حالة الوثائق المطلوبة (اختياري)
        
        Returns:
            قائمة الوثائق
        """
        try:
            query = self.supabase.table("documents").select("*")
            
            if status:
                query = query.eq("status", status)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            print(f"خطأ في جلب الوثائق: {e}")
            return []
    
    def get_document_content(self, document_id: str) -> List[Dict]:
        """
        الحصول على محتوى الوثيقة
        
        Args:
            document_id: معرف الوثيقة
        
        Returns:
            قائمة صفحات المحتوى
        """
        try:
            result = self.supabase.table("document_content").select("*").eq("document_id", document_id).order("page_number").execute()
            return result.data or []
            
        except Exception as e:
            print(f"خطأ في جلب محتوى الوثيقة: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        حذف وثيقة وجميع بياناتها المرتبطة
        
        Args:
            document_id: معرف الوثيقة
        
        Returns:
            True إذا تم الحذف بنجاح
        """
        try:
            # حذف الفهارس
            self.supabase.table("document_index").delete().eq("document_id", document_id).execute()
            
            # حذف المحتوى
            self.supabase.table("document_content").delete().eq("document_id", document_id).execute()
            
            # حذف الوثيقة
            result = self.supabase.table("documents").delete().eq("id", document_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"خطأ في حذف الوثيقة: {e}")
            return False
    
    def search_documents(self, search_term: str) -> List[Dict]:
        """
        البحث في الوثائق (بحث أساسي)
        
        Args:
            search_term: مصطلح البحث
        
        Returns:
            قائمة الوثائق المطابقة
        """
        try:
            # البحث في أسماء الملفات
            result = self.supabase.table("documents").select("*").ilike("filename", f"%{search_term}%").execute()
            return result.data or []
            
        except Exception as e:
            print(f"خطأ في البحث: {e}")
            return []
    
    def upload_pdf_file(self, file_path: str, custom_filename: str = None) -> str:
        """
        رفع ملف PDF إلى Supabase Storage وإنشاء سجل في قاعدة البيانات
        
        Args:
            file_path: مسار الملف المحلي
            custom_filename: اسم مخصص للملف (اختياري)
        
        Returns:
            معرف الوثيقة الجديدة
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"الملف غير موجود: {file_path}")
            
            # تحضير معلومات الملف
            file_size = os.path.getsize(file_path)
            original_filename = os.path.basename(file_path)
            
            # إنشاء اسم فريد للملف
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # اسم الملف الموحد (نفس الاسم في قاعدة البيانات و Storage)
            if custom_filename:
                filename = f"{timestamp}_{custom_filename}"
            else:
                filename = f"{timestamp}_{original_filename}"
            
            storage_path = f"documents/{filename}"
            
            # قراءة الملف
            with open(file_path, 'rb') as file:
                file_content = file.read()
            
            # رفع الملف إلى Storage
            storage_result = self.supabase.storage.from_("documents").upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": "application/pdf"}
            )
            
            if hasattr(storage_result, 'error') and storage_result.error:
                raise Exception(f"فشل رفع الملف: {storage_result.error}")
            
            # إنشاء سجل في قاعدة البيانات
            document_id = self.create_document(
                filename=filename,
                original_path=file_path,
                file_size=file_size,
                metadata={"storage_path": storage_path}
            )
            
            print(f"✅ تم رفع الملف بنجاح: {filename}")
            print(f"📁 مسار Storage: {storage_path}")
            print(f"🆔 معرف الوثيقة: {document_id}")
            print(f"🔗 الاسم موحد في قاعدة البيانات و Storage")
            
            return document_id
            
        except Exception as e:
            print(f"❌ خطأ في رفع الملف: {e}")
            raise
    
    def trigger_processing(self, document_id: str, file_path: str, filename: str) -> bool:
        """
        استدعاء Edge Function لمعالجة الوثيقة
        
        Args:
            document_id: معرف الوثيقة
            file_path: مسار الملف (للمعلومات)
            filename: اسم الملف
        
        Returns:
            True إذا تم استدعاء المعالجة بنجاح
        """
        try:
            # تحديث حالة الوثيقة إلى "processing"
            self.update_document_status(document_id, "processing")
            
            # جلب اسم الملف الموحد من قاعدة البيانات
            doc_result = self.supabase.table("documents").select("filename").eq("id", document_id).execute()
            
            unified_filename = filename  # افتراضي
            if doc_result.data:
                unified_filename = doc_result.data[0]["filename"]
                print(f"🔗 استخدام الاسم الموحد: {unified_filename}")
            
            # مسار Storage باستخدام الاسم الموحد
            storage_path = f"documents/{unified_filename}"
            
            # بيانات الطلب للـ Edge Function
            payload = {
                "documentId": document_id,
                "filePath": storage_path,  # مسار Storage الصحيح
                "fileName": unified_filename
            }
            
            # استدعاء Edge Function
            edge_function_url = f"{self.url}/functions/v1/process-document"
            headers = {
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json"
            }
            
            print(f"🔄 بدء معالجة الوثيقة: {filename}")
            
            response = requests.post(
                edge_function_url,
                json=payload,
                headers=headers,
                timeout=300  # 5 دقائق timeout
            )
            
            if response.status_code == 200:
                print(f"✅ تم استدعاء المعالجة بنجاح للوثيقة: {document_id}")
                return True
            else:
                print(f"⚠️ فشل استدعاء Edge Function: {response.status_code}")
                print(f"📄 الرد: {response.text}")
                self.update_document_status(document_id, "failed")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في استدعاء المعالجة: {e}")
            self.update_document_status(document_id, "failed")
            return False
    
    def check_processing_status(self, document_id: str) -> str:
        """
        فحص حالة معالجة الوثيقة
        
        Args:
            document_id: معرف الوثيقة
        
        Returns:
            حالة المعالجة: 'uploaded', 'processing', 'completed', 'failed'
        """
        try:
            result = self.supabase.table("documents").select("status").eq("id", document_id).execute()
            
            if result.data:
                status = result.data[0]["status"]
                print(f"📊 حالة الوثيقة {document_id}: {status}")
                return status
            else:
                print(f"❌ لم يتم العثور على الوثيقة: {document_id}")
                return "not_found"
                
        except Exception as e:
            print(f"❌ خطأ في فحص حالة المعالجة: {e}")
            return "error"
    
    def get_processed_document_info(self, document_id: str) -> Optional[Dict]:
        """
        جلب معلومات الوثيقة المعالجة مع الإحصائيات
        
        Args:
            document_id: معرف الوثيقة
        
        Returns:
            معلومات الوثيقة والإحصائيات أو None
        """
        try:
            # جلب معلومات الوثيقة الأساسية
            doc_result = self.supabase.table("documents").select("*").eq("id", document_id).execute()
            
            if not doc_result.data:
                print(f"❌ لم يتم العثور على الوثيقة: {document_id}")
                return None
            
            document_info = doc_result.data[0]
            
            # جلب محتوى الوثيقة
            content_result = self.supabase.table("document_content").select("*").eq("document_id", document_id).execute()
            
            # جلب فهارس الوثيقة
            index_result = self.supabase.table("document_index").select("*").eq("document_id", document_id).execute()
            
            # إعداد الإحصائيات
            stats = {
                "total_pages": len(content_result.data) if content_result.data else 0,
                "total_indexes": len(index_result.data) if index_result.data else 0,
                "file_size_mb": round(document_info.get("file_size", 0) / (1024 * 1024), 2),
                "upload_date": document_info.get("upload_date"),
                "status": document_info.get("status"),
                "extracted_title": document_info.get("extracted_title"),
                "document_type": document_info.get("document_type", "غير محدد"),
                "content_quality_score": document_info.get("content_quality_score", 0.0)
            }
            
            # دمج المعلومات
            full_info = {
                "document": document_info,
                "content": content_result.data if content_result.data else [],
                "indexes": index_result.data if index_result.data else [],
                "statistics": stats
            }
            
            print(f"📋 معلومات الوثيقة {document_id}:")
            print(f"   📄 الاسم: {document_info.get('filename')}")
            print(f"   📊 الحالة: {stats['status']}")
            print(f"   📑 عدد الصفحات: {stats['total_pages']}")
            print(f"   🔍 عدد الفهارس: {stats['total_indexes']}")
            print(f"   💾 الحجم: {stats['file_size_mb']} MB")
            
            return full_info
            
        except Exception as e:
            print(f"❌ خطأ في جلب معلومات الوثيقة: {e}")
            return None

# إنشاء مثيل عام للاستخدام
try:
    db_manager = SupabaseManager()
    print("✅ تم تهيئة الاتصال مع Supabase بنجاح")
except Exception as e:
    print(f"❌ فشل في الاتصال مع Supabase: {e}")
    db_manager = None
