"""
نظام الفهرسة للنصوص العربية
يستخرج الكلمات المفتاحية ويقسم النص إلى أجزاء قابلة للبحث
"""

import re
import string
from typing import List, Dict, Tuple
from collections import Counter

class ArabicTextIndexer:
    """فهرسة النصوص العربية"""
    
    def __init__(self):
        """تهيئة المفهرس"""
        # كلمات الوقف العربية الشائعة
        self.stop_words = {
            'في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك',
            'التي', 'الذي', 'التي', 'اللذان', 'اللتان', 'اللذين', 'اللتين', 'اللواتي',
            'أن', 'إن', 'كان', 'كانت', 'يكون', 'تكون', 'سوف', 'قد', 'لقد',
            'ما', 'لا', 'ليس', 'غير', 'سوى', 'بل', 'لكن', 'إلا', 'حتى',
            'أو', 'أم', 'إما', 'كل', 'بعض', 'جميع', 'كلا', 'كلتا',
            'هو', 'هي', 'هم', 'هن', 'أنت', 'أنتم', 'أنتن', 'أنا', 'نحن',
            'له', 'لها', 'لهم', 'لهن', 'بك', 'بها', 'بهم', 'بهن'
        }
        
        # علامات الترقيم العربية والإنجليزية
        self.punctuation = string.punctuation + '،؛؟!'
    
    def clean_text(self, text: str) -> str:
        """
        تنظيف النص من علامات الترقيم والرموز غير المرغوبة
        
        Args:
            text: النص المراد تنظيفه
        
        Returns:
            النص المنظف
        """
        # إزالة علامات الترقيم
        text = re.sub(f'[{re.escape(self.punctuation)}]', ' ', text)
        
        # إزالة الأرقام الإنجليزية والعربية
        text = re.sub(r'[0-9٠-٩]', ' ', text)
        
        # إزالة المسافات الزائدة
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_words(self, text: str) -> List[str]:
        """
        استخراج الكلمات من النص
        
        Args:
            text: النص المراد معالجته
        
        Returns:
            قائمة الكلمات
        """
        # تنظيف النص
        clean_text = self.clean_text(text)
        
        # تقسيم النص إلى كلمات
        words = clean_text.split()
        
        # تصفية الكلمات
        filtered_words = []
        for word in words:
            # إزالة الكلمات القصيرة جداً (أقل من حرفين)
            if len(word) < 2:
                continue
            
            # إزالة كلمات الوقف
            if word in self.stop_words:
                continue
            
            # إضافة الكلمة المنظفة
            filtered_words.append(word)
        
        return filtered_words
    
    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """
        استخراج الكلمات المفتاحية الأكثر تكراراً
        
        Args:
            text: النص المراد معالجته
            max_keywords: العدد الأقصى للكلمات المفتاحية
        
        Returns:
            قائمة الكلمات المفتاحية مرتبة حسب الأهمية
        """
        words = self.extract_words(text)
        
        # حساب تكرار الكلمات
        word_freq = Counter(words)
        
        # الحصول على أكثر الكلمات تكراراً
        most_common = word_freq.most_common(max_keywords)
        
        return [word for word, freq in most_common]
    
    def chunk_text(self, text: str, chunk_size: int = 500) -> List[Dict]:
        """
        تقسيم النص إلى أجزاء منطقية
        
        Args:
            text: النص المراد تقسيمه
            chunk_size: حجم الجزء بالأحرف
        
        Returns:
            قائمة الأجزاء مع معلومات إضافية
        """
        # تقسيم النص إلى فقرات
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        chunk_position = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # إذا كانت الفقرة مع الجزء الحالي تتجاوز الحد الأقصى
            if len(current_chunk + paragraph) > chunk_size and current_chunk:
                # حفظ الجزء الحالي
                if current_chunk:
                    keywords = self.extract_keywords(current_chunk, 10)
                    chunks.append({
                        'content': current_chunk.strip(),
                        'keywords': keywords,
                        'position': chunk_position,
                        'length': len(current_chunk)
                    })
                    chunk_position += 1
                
                # بدء جزء جديد
                current_chunk = paragraph + '\n\n'
            else:
                # إضافة الفقرة إلى الجزء الحالي
                current_chunk += paragraph + '\n\n'
        
        # حفظ الجزء الأخير
        if current_chunk:
            keywords = self.extract_keywords(current_chunk, 10)
            chunks.append({
                'content': current_chunk.strip(),
                'keywords': keywords,
                'position': chunk_position,
                'length': len(current_chunk)
            })
        
        return chunks
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        استخراج الكيانات المهمة من النص (أسماء، تواريخ، أرقام)
        
        Args:
            text: النص المراد معالجته
        
        Returns:
            قاموس الكيانات المستخرجة
        """
        entities = {
            'dates': [],
            'numbers': [],
            'proper_nouns': []
        }
        
        # استخراج التواريخ العربية
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # 12/5/2023
            r'\d{1,2}-\d{1,2}-\d{4}',  # 12-5-2023
            r'[٠-٩]{1,2}/[٠-٩]{1,2}/[٠-٩]{4}',  # تواريخ عربية
        ]
        
        for pattern in date_patterns:
            dates = re.findall(pattern, text)
            entities['dates'].extend(dates)
        
        # استخراج الأرقام
        number_patterns = [
            r'\d+',  # أرقام إنجليزية
            r'[٠-٩]+',  # أرقام عربية
        ]
        
        for pattern in number_patterns:
            numbers = re.findall(pattern, text)
            entities['numbers'].extend(numbers)
        
        # استخراج الأسماء العلم (كلمات تبدأ بحرف كبير)
        proper_noun_pattern = r'\b[A-Z][a-zA-Z]+\b'
        proper_nouns = re.findall(proper_noun_pattern, text)
        entities['proper_nouns'] = list(set(proper_nouns))
        
        return entities
    
    def create_full_index(self, text: str, document_id: str = None) -> Dict:
        """
        إنشاء فهرس شامل للنص
        
        Args:
            text: النص المراد فهرسته
            document_id: معرف الوثيقة (اختياري)
        
        Returns:
            الفهرس الشامل
        """
        # تقسيم النص إلى أجزاء
        chunks = self.chunk_text(text)
        
        # استخراج الكلمات المفتاحية العامة
        global_keywords = self.extract_keywords(text, 30)
        
        # استخراج الكيانات
        entities = self.extract_entities(text)
        
        # إحصائيات النص
        words = self.extract_words(text)
        stats = {
            'total_words': len(words),
            'unique_words': len(set(words)),
            'total_chars': len(text),
            'chunks_count': len(chunks)
        }
        
        return {
            'document_id': document_id,
            'global_keywords': global_keywords,
            'entities': entities,
            'chunks': chunks,
            'statistics': stats,
            'created_at': None  # سيتم تعيينها في قاعدة البيانات
        }

# إنشاء مثيل عام للاستخدام
text_indexer = ArabicTextIndexer()
