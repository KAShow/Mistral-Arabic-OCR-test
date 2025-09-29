"""
نظام التخزين المحلي بصيغة JSON
يستبدل قاعدة البيانات بملفات JSON محلية منظمة
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

class JSONStorage:
    """مدير التخزين المحلي بصيغة JSON"""
    
    def __init__(self, base_dir: str = "json_data"):
        """
        تهيئة نظام التخزين المحلي
        
        Args:
            base_dir: المجلد الأساسي لتخزين الملفات
        """
        self.base_dir = Path(base_dir)
        self.documents_dir = self.base_dir / "documents"
        self.content_dir = self.base_dir / "content"
        self.indexes_dir = self.base_dir / "indexes"
        self.metadata_file = self.base_dir / "metadata.json"
        
        # إنشاء المجلدات المطلوبة
        self.ensure_directories()
        
        # تحميل أو إنشاء ملف البيانات الوصفية الرئيسي
        self.metadata = self.load_metadata()
    
    def ensure_directories(self):
        """التأكد من وجود جميع المجلدات المطلوبة"""
        for directory in [self.base_dir, self.documents_dir, self.content_dir, self.indexes_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ تم إنشاء بنية المجلدات في: {self.base_dir}")
    
    def load_metadata(self) -> Dict:
        """تحميل البيانات الوصفية الرئيسية"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # إنشاء ملف بيانات وصفية جديد
        return {
            "created_at": datetime.now().isoformat(),
            "total_documents": 0,
            "last_updated": datetime.now().isoformat(),
            "documents": {}
        }
    
    def save_metadata(self):
        """حفظ البيانات الوصفية الرئيسية"""
        self.metadata["last_updated"] = datetime.now().isoformat()
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
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
            # إنشاء معرف فريد
            document_id = str(uuid.uuid4())
            
            # بيانات الوثيقة
            document_data = {
                "id": document_id,
                "filename": filename,
                "original_path": original_path,
                "file_size": file_size,
                "status": "uploaded",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # حفظ بيانات الوثيقة في ملف منفصل
            doc_file = self.documents_dir / f"{document_id}.json"
            with open(doc_file, 'w', encoding='utf-8') as f:
                json.dump(document_data, f, ensure_ascii=False, indent=2)
            
            # تحديث البيانات الوصفية الرئيسية
            self.metadata["documents"][document_id] = {
                "filename": filename,
                "status": "uploaded",
                "created_at": document_data["created_at"],
                "file_size": file_size
            }
            self.metadata["total_documents"] += 1
            self.save_metadata()
            
            print(f"✅ تم إنشاء سجل الوثيقة: {filename} (ID: {document_id})")
            return document_id
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء الوثيقة: {e}")
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
            doc_file = self.documents_dir / f"{document_id}.json"
            
            if not doc_file.exists():
                print(f"❌ الوثيقة غير موجودة: {document_id}")
                return False
            
            # تحميل بيانات الوثيقة
            with open(doc_file, 'r', encoding='utf-8') as f:
                document_data = json.load(f)
            
            # تحديث الحالة
            document_data["status"] = status
            document_data["updated_at"] = datetime.now().isoformat()
            
            # حفظ البيانات المحدثة
            with open(doc_file, 'w', encoding='utf-8') as f:
                json.dump(document_data, f, ensure_ascii=False, indent=2)
            
            # تحديث البيانات الوصفية الرئيسية
            if document_id in self.metadata["documents"]:
                self.metadata["documents"][document_id]["status"] = status
                self.save_metadata()
            
            print(f"✅ تم تحديث حالة الوثيقة {document_id} إلى: {status}")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في تحديث حالة الوثيقة: {e}")
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
            # إنشاء معرف فريد لمحتوى الصفحة
            content_id = str(uuid.uuid4())
            
            # بيانات المحتوى
            content_data = {
                "id": content_id,
                "document_id": document_id,
                "page_number": page_number,
                "raw_markdown": raw_markdown,
                "processed_text": processed_text or raw_markdown,
                "created_at": datetime.now().isoformat()
            }
            
            # مسار ملف المحتوى
            content_file = self.content_dir / f"{document_id}_page_{page_number:03d}.json"
            
            with open(content_file, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ تم حفظ محتوى الصفحة {page_number} للوثيقة {document_id}")
            return content_id
            
        except Exception as e:
            print(f"❌ خطأ في حفظ المحتوى: {e}")
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
            # إنشاء معرف فريد للفهرس
            index_id = str(uuid.uuid4())
            
            # بيانات الفهرس
            index_data = {
                "id": index_id,
                "document_id": document_id,
                "content_chunk": content_chunk,
                "keywords": keywords,
                "chunk_position": chunk_position,
                "created_at": datetime.now().isoformat()
            }
            
            # مسار ملف الفهرس
            index_file = self.indexes_dir / f"{document_id}_chunk_{chunk_position:03d}.json"
            
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ تم إنشاء فهرس الجزء {chunk_position} للوثيقة {document_id}")
            return index_id
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء الفهرس: {e}")
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
            for doc_id, doc_info in self.metadata["documents"].items():
                if doc_info["filename"] == filename:
                    # تحميل البيانات الكاملة للوثيقة
                    doc_file = self.documents_dir / f"{doc_id}.json"
                    if doc_file.exists():
                        with open(doc_file, 'r', encoding='utf-8') as f:
                            return json.load(f)
            return None
            
        except Exception as e:
            print(f"❌ خطأ في البحث عن الوثيقة: {e}")
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
            documents = []
            
            for doc_id, doc_info in self.metadata["documents"].items():
                if status is None or doc_info["status"] == status:
                    # تحميل البيانات الكاملة للوثيقة
                    doc_file = self.documents_dir / f"{doc_id}.json"
                    if doc_file.exists():
                        with open(doc_file, 'r', encoding='utf-8') as f:
                            documents.append(json.load(f))
            
            return documents
            
        except Exception as e:
            print(f"❌ خطأ في جلب الوثائق: {e}")
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
            content = []
            
            # البحث عن جميع ملفات المحتوى للوثيقة
            pattern = f"{document_id}_page_*.json"
            for content_file in self.content_dir.glob(pattern):
                with open(content_file, 'r', encoding='utf-8') as f:
                    content.append(json.load(f))
            
            # ترتيب المحتوى حسب رقم الصفحة
            content.sort(key=lambda x: x.get('page_number', 0))
            return content
            
        except Exception as e:
            print(f"❌ خطأ في جلب محتوى الوثيقة: {e}")
            return []
    
    def save_complete_document(self, document_id: str, filename: str, content: Dict):
        """
        حفظ وثيقة كاملة بجميع بياناتها في ملف JSON واحد شامل
        
        Args:
            document_id: معرف الوثيقة
            filename: اسم الملف
            content: بيانات الوثيقة الكاملة (النص، الفهارس، إلخ)
        """
        try:
            # إنشاء البيانات الشاملة
            complete_data = {
                "document_info": {
                    "id": document_id,
                    "filename": filename,
                    "processed_at": datetime.now().isoformat(),
                    "status": "completed"
                },
                "content": content
            }
            
            # حفظ الوثيقة الكاملة
            complete_file = self.base_dir / f"{filename.replace('.pdf', '_complete.json')}"
            with open(complete_file, 'w', encoding='utf-8') as f:
                json.dump(complete_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ تم حفظ الوثيقة الكاملة: {complete_file}")
            
        except Exception as e:
            print(f"❌ خطأ في حفظ الوثيقة الكاملة: {e}")
            raise
    
    def get_processing_statistics(self) -> Dict:
        """الحصول على إحصائيات المعالجة"""
        try:
            stats = {
                'total': 0,
                'completed': 0,
                'processing': 0,
                'failed': 0,
                'uploaded': 0
            }
            
            for doc_info in self.metadata["documents"].values():
                stats['total'] += 1
                status = doc_info.get('status', 'unknown')
                if status in stats:
                    stats[status] += 1
            
            return stats
            
        except Exception as e:
            print(f"❌ خطأ في حساب الإحصائيات: {e}")
            return {'total': 0, 'completed': 0, 'processing': 0, 'failed': 0, 'uploaded': 0}

# إنشاء مثيل عام للاستخدام
json_storage = JSONStorage()
print(f"✅ تم تهيئة نظام التخزين JSON بنجاح في: {json_storage.base_dir}")
