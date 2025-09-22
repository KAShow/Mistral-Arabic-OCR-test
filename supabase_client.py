"""
عميل Supabase للتفاعل مع قاعدة البيانات
يدير العمليات الأساسية للوثائق والمحتوى والفهرسة
"""

import os
import json
import uuid
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

# إنشاء مثيل عام للاستخدام
try:
    db_manager = SupabaseManager()
    print("✅ تم تهيئة الاتصال مع Supabase بنجاح")
except Exception as e:
    print(f"❌ فشل في الاتصال مع Supabase: {e}")
    db_manager = None
