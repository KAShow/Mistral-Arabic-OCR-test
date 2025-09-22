"""
معالج النصوص المتقدم الشامل
يدمج جميع عمليات التحسين والمعالجة في واجهة موحدة
"""

from typing import List, Dict, Optional, Any
from content_cleaner import content_cleaner
from title_extractor import title_extractor
from legal_indexer import legal_indexer

class AdvancedTextProcessor:
    """معالج النصوص المتقدم الشامل"""
    
    def __init__(self):
        """تهيئة المعالج المتقدم"""
        self.cleaner = content_cleaner
        self.title_extractor = title_extractor
        self.indexer = legal_indexer
    
    def process_document_pages(self, pages_content: List[str], filename: str = None) -> Dict:
        """معالجة شاملة لصفحات الوثيقة"""
        if not pages_content:
            return self._empty_result()
        
        # 1. تنظيف جميع الصفحات
        print("🧹 تنظيف محتوى الصفحات...")
        cleaned_pages = self.cleaner.clean_page_content(pages_content)
        cleaning_stats = self.cleaner.get_cleaning_statistics(cleaned_pages)
        
        # 2. استخراج العنوان
        print("📝 استخراج العنوان...")
        title_result = self.title_extractor.extract_title_from_pages(pages_content)
        
        # 3. دمج المحتوى المفيد
        useful_content = self._merge_useful_content(cleaned_pages)
        
        if not useful_content:
            return self._empty_result(cleaning_stats, title_result)
        
        # 4. الفهرسة المتقدمة
        print("📚 إنشاء الفهرس المتقدم...")
        index_result = self.indexer.create_comprehensive_index(useful_content)
        
        # 5. تقييم جودة الوثيقة
        quality_score = self._calculate_document_quality(
            cleaning_stats, title_result, index_result
        )
        
        # 6. إنشاء التقرير الشامل
        return {
            'filename': filename,
            'title': title_result,
            'content': {
                'full_text': useful_content,
                'pages_count': len(pages_content),
                'useful_pages_count': cleaning_stats['useful_pages'],
                'total_length': len(useful_content)
            },
            'cleaning': cleaning_stats,
            'indexing': index_result,
            'quality': {
                'overall_score': quality_score,
                'title_quality': self.title_extractor.calculate_title_quality_score(title_result),
                'content_quality': cleaning_stats['useful_pages_ratio'],
                'indexing_confidence': index_result['overall_confidence']
            },
            'processing_summary': self._create_processing_summary(
                cleaning_stats, title_result, index_result, quality_score
            )
        }
    
    def _merge_useful_content(self, cleaned_pages: List[Dict]) -> str:
        """دمج المحتوى المفيد من الصفحات"""
        useful_pages = [
            page for page in cleaned_pages 
            if page['is_useful'] and len(page['cleaned_text'].strip()) > 20
        ]
        
        if not useful_pages:
            return ""
        
        merged_content = []
        for page in useful_pages:
            content = page['cleaned_text'].strip()
            if content:
                merged_content.append(f"## صفحة {page['page_number']}\n\n{content}")
        
        return '\n\n'.join(merged_content)
    
    def _calculate_document_quality(self, cleaning_stats: Dict, title_result: Dict, index_result: Dict) -> float:
        """حساب درجة جودة الوثيقة الإجمالية"""
        scores = []
        
        # درجة التنظيف (30%)
        cleaning_score = cleaning_stats.get('useful_pages_ratio', 0) * 0.3
        scores.append(cleaning_score)
        
        # درجة العنوان (25%)
        title_score = self.title_extractor.calculate_title_quality_score(title_result) * 0.25
        scores.append(title_score)
        
        # درجة الفهرسة (25%)
        indexing_score = index_result.get('overall_confidence', 0) * 0.25
        scores.append(indexing_score)
        
        # درجة الهيكل القانوني (20%)
        structure_score = self._calculate_structure_score(index_result) * 0.2
        scores.append(structure_score)
        
        return sum(scores)
    
    def _calculate_structure_score(self, index_result: Dict) -> float:
        """حساب درجة الهيكل القانوني"""
        structure = index_result.get('legal_structure', {})
        stats = index_result.get('statistics', {})
        
        score = 0.0
        
        # وجود مواد قانونية
        if 'مادة' in structure and len(structure['مادة']) > 0:
            score += 0.4
        
        # وجود فصول
        if 'فصل' in structure and len(structure['فصل']) > 0:
            score += 0.2
        
        # وجود أبواب
        if 'باب' in structure and len(structure['باب']) > 0:
            score += 0.2
        
        # وجود أرقام قانونية
        legal_numbers = index_result.get('legal_numbers', {})
        if legal_numbers and any(len(nums) > 0 for nums in legal_numbers.values()):
            score += 0.2
        
        return min(score, 1.0)
    
    def _create_processing_summary(self, cleaning_stats: Dict, title_result: Dict, 
                                 index_result: Dict, quality_score: float) -> Dict:
        """إنشاء ملخص عملية المعالجة"""
        return {
            'status': 'success' if quality_score > 0.3 else 'low_quality',
            'improvements_applied': cleaning_stats.get('improvement_counts', {}),
            'title_extracted': bool(title_result.get('title')),
            'title_source': title_result.get('source', 'unknown'),
            'structure_detected': {
                'articles': len(index_result.get('legal_structure', {}).get('مادة', [])),
                'chapters': len(index_result.get('legal_structure', {}).get('فصل', [])),
                'sections': len(index_result.get('legal_structure', {}).get('باب', []))
            },
            'keywords_extracted': len(index_result.get('keywords', [])),
            'chunks_created': len(index_result.get('chunks', [])),
            'recommendations': self._generate_recommendations(quality_score, title_result, index_result)
        }
    
    def _generate_recommendations(self, quality_score: float, title_result: Dict, index_result: Dict) -> List[str]:
        """توليد توصيات لتحسين الوثيقة"""
        recommendations = []
        
        if quality_score < 0.5:
            recommendations.append("جودة الوثيقة منخفضة - يُنصح بمراجعة الملف الأصلي")
        
        if not title_result.get('title'):
            recommendations.append("لم يتم استخراج عنوان - قد تحتاج لتحديد العنوان يدوياً")
        
        if title_result.get('confidence', 0) < 0.7:
            recommendations.append("ثقة العنوان منخفضة - يُنصح بمراجعة العنوان المستخرج")
        
        structure = index_result.get('legal_structure', {})
        if not structure.get('مادة'):
            recommendations.append("لم يتم اكتشاف مواد قانونية - قد تكون الوثيقة غير قانونية أو تحتاج معالجة خاصة")
        
        keywords_count = len(index_result.get('keywords', []))
        if keywords_count < 10:
            recommendations.append("عدد الكلمات المفتاحية قليل - قد يؤثر على جودة البحث")
        
        if index_result.get('overall_confidence', 0) < 0.3:
            recommendations.append("ثقة الفهرسة منخفضة - قد تحتاج لمعالجة إضافية")
        
        return recommendations
    
    def _empty_result(self, cleaning_stats: Dict = None, title_result: Dict = None) -> Dict:
        """نتيجة فارغة في حالة فشل المعالجة"""
        return {
            'filename': None,
            'title': title_result or {'title': None, 'confidence': 0},
            'content': {
                'full_text': '',
                'pages_count': 0,
                'useful_pages_count': 0,
                'total_length': 0
            },
            'cleaning': cleaning_stats or {},
            'indexing': {
                'keywords': [],
                'keyword_categories': {},
                'legal_structure': {},
                'legal_numbers': {},
                'chunks': [],
                'statistics': {},
                'overall_confidence': 0
            },
            'quality': {
                'overall_score': 0,
                'title_quality': 0,
                'content_quality': 0,
                'indexing_confidence': 0
            },
            'processing_summary': {
                'status': 'failed',
                'improvements_applied': {},
                'title_extracted': False,
                'recommendations': ['فشل في معالجة الوثيقة - يرجى التحقق من الملف الأصلي']
            }
        }
    
    def process_for_database_storage(self, pages_content: List[str], filename: str = None) -> Dict:
        """معالجة خاصة للتخزين في قاعدة البيانات"""
        # المعالجة الشاملة
        result = self.process_document_pages(pages_content, filename)
        
        # تحضير البيانات للتخزين
        document_data = {
            'filename': filename,
            'extracted_title': result['title'].get('full_title'),
            'document_type': self.title_extractor.extract_document_type(
                result['title'].get('title', '')
            ),
            'content_quality_score': result['quality']['overall_score'],
            'processing_notes': {
                'improvements': result['cleaning'].get('improvement_counts', {}),
                'title_confidence': result['title'].get('confidence', 0),
                'recommendations': result['processing_summary'].get('recommendations', [])
            }
        }
        
        # محتوى الصفحات المنظف
        pages_data = []
        for page in result['cleaning'].get('cleaned_pages', []):
            if page['is_useful']:
                pages_data.append({
                    'page_number': page['page_number'],
                    'raw_markdown': pages_content[page['page_number'] - 1] if page['page_number'] <= len(pages_content) else '',
                    'cleaned_content': page['cleaned_text'],
                    'has_images': 'تم إزالة مراجع الصور' in page.get('improvements', []),
                    'content_type': 'نص' if page['is_useful'] else 'غير مفيد'
                })
        
        # بيانات الفهرسة
        indexing_data = []
        for chunk in result['indexing'].get('chunks', []):
            indexing_data.append({
                'content_chunk': chunk['content'],
                'keywords': chunk.get('keywords', []),
                'chunk_position': chunk.get('chunk_id', 0),
                'chunk_type': chunk.get('type', 'paragraph_group'),
                'confidence': chunk.get('confidence', 0)
            })
        
        return {
            'document': document_data,
            'pages': pages_data,
            'indexing': indexing_data,
            'full_result': result  # للمراجعة والتشخيص
        }

# إنشاء مثيل عام للاستخدام
advanced_processor = AdvancedTextProcessor()
