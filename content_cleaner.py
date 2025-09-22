"""
محسن تنظيف النصوص - إزالة مراجع الصور وتنسيق LaTeX وتحسين النص العربي
"""

import re
from typing import List, Dict, Tuple

class ContentCleaner:
    """منظف المحتوى المتقدم للنصوص العربية والوثائق القانونية"""
    
    def __init__(self):
        """تهيئة المنظف"""
        # أنماط مراجع الصور
        self.image_patterns = [
            r'!\[img-\d+\.jpeg\]\(img-\d+\.jpeg\)',  # ![img-0.jpeg](img-0.jpeg)
            r'!\[.*?\]\(.*?\.(?:jpg|jpeg|png|gif)\)',  # أي مرجع صورة
            r'<img[^>]*>',  # علامات HTML للصور
        ]
        
        # أنماط LaTeX والرياضيات
        self.latex_patterns = [
            r'\$\$[^$]*\$\$',  # $$...$$
            r'\\begin\{aligned\}.*?\\end\{aligned\}',  # \begin{aligned}...\end{aligned}
            r'\\text\{([^}]*)\}',  # \text{...} - نحتفظ بالنص داخل الأقواس
            r'\\[a-zA-Z]+\{[^}]*\}',  # أوامر LaTeX الأخرى
            r'\\[a-zA-Z]+',  # أوامر LaTeX بسيطة
            r'\$[^$]*\$',  # $...$
        ]
        
        # أنماط التنسيق غير المرغوبة
        self.formatting_patterns = [
            r'\s+',  # مسافات متعددة
            r'\n\s*\n\s*\n+',  # أسطر فارغة متعددة
            r'^\s+|\s+$',  # مسافات في بداية ونهاية السطر
        ]
        
        # كلمات مؤشرة للمحتوى غير المفيد
        self.useless_indicators = [
            'img-',
            'image',
            'صورة',
            'الصفحة فارغة',
            'لا يوجد نص'
        ]
    
    def clean_images(self, text: str) -> str:
        """إزالة جميع مراجع الصور من النص"""
        cleaned_text = text
        
        for pattern in self.image_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        return cleaned_text
    
    def clean_latex(self, text: str) -> str:
        """تنظيف تنسيق LaTeX والرياضيات"""
        cleaned_text = text
        
        # استخراج النص من \text{...} قبل حذفه
        text_matches = re.findall(r'\\text\{([^}]*)\}', cleaned_text)
        for match in text_matches:
            cleaned_text = cleaned_text.replace(f'\\text{{{match}}}', match)
        
        # حذف باقي أنماط LaTeX
        for pattern in self.latex_patterns:
            if pattern != r'\\text\{([^}]*)\}':  # تم معالجته بالفعل
                cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.DOTALL)
        
        return cleaned_text
    
    def clean_formatting(self, text: str) -> str:
        """تنظيف التنسيق والمسافات"""
        cleaned_text = text
        
        # توحيد المسافات المتعددة
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        # تنظيف الأسطر الفارغة المتعددة
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
        
        # إزالة المسافات من بداية ونهاية الأسطر
        lines = cleaned_text.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        cleaned_text = '\n'.join(cleaned_lines)
        
        return cleaned_text
    
    def clean_arabic_text(self, text: str) -> str:
        """تحسين النص العربي"""
        cleaned_text = text
        
        # إصلاح علامات الترقيم العربية
        replacements = {
            '،،': '،',  # فواصل مكررة
            '..': '.',   # نقاط مكررة
            '؟؟': '؟',   # علامات استفهام مكررة
            '!!': '!',   # علامات تعجب مكررة
        }
        
        for old, new in replacements.items():
            cleaned_text = cleaned_text.replace(old, new)
        
        # تنظيف الأرقام والتواريخ
        cleaned_text = re.sub(r'\(\s*(\d+)\s*\)', r'(\1)', cleaned_text)  # (  5  ) → (5)
        
        return cleaned_text
    
    def remove_empty_lines(self, text: str) -> str:
        """إزالة الأسطر الفارغة أو التي تحتوي على مسافات فقط"""
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        return '\n'.join(non_empty_lines)
    
    def is_content_useful(self, text: str) -> bool:
        """تحديد ما إذا كان المحتوى مفيداً أم لا"""
        if not text or len(text.strip()) < 10:
            return False
        
        # فحص المؤشرات غير المفيدة
        text_lower = text.lower()
        for indicator in self.useless_indicators:
            if indicator in text_lower:
                return False
        
        # فحص نسبة النص المفيد
        useful_chars = len(re.sub(r'[^\w\s\u0600-\u06FF]', '', text, flags=re.UNICODE))
        total_chars = len(text)
        
        if total_chars > 0 and (useful_chars / total_chars) < 0.3:
            return False
        
        return True
    
    def clean_content(self, text: str) -> Dict[str, any]:
        """تنظيف شامل للمحتوى مع تقرير التحسينات"""
        if not text:
            return {
                'cleaned_text': '',
                'is_useful': False,
                'improvements': [],
                'original_length': 0,
                'cleaned_length': 0
            }
        
        original_length = len(text)
        improvements = []
        
        # 1. إزالة مراجع الصور
        before_images = text
        text = self.clean_images(text)
        if len(text) != len(before_images):
            improvements.append('تم إزالة مراجع الصور')
        
        # 2. تنظيف LaTeX
        before_latex = text
        text = self.clean_latex(text)
        if len(text) != len(before_latex):
            improvements.append('تم تنظيف تنسيق LaTeX')
        
        # 3. تنظيف التنسيق
        before_formatting = text
        text = self.clean_formatting(text)
        if len(text) != len(before_formatting):
            improvements.append('تم تحسين التنسيق')
        
        # 4. تحسين النص العربي
        before_arabic = text
        text = self.clean_arabic_text(text)
        if len(text) != len(before_arabic):
            improvements.append('تم تحسين النص العربي')
        
        # 5. إزالة الأسطر الفارغة
        before_empty = text
        text = self.remove_empty_lines(text)
        if len(text) != len(before_empty):
            improvements.append('تم إزالة الأسطر الفارغة')
        
        # تقييم فائدة المحتوى
        is_useful = self.is_content_useful(text)
        
        return {
            'cleaned_text': text.strip(),
            'is_useful': is_useful,
            'improvements': improvements,
            'original_length': original_length,
            'cleaned_length': len(text),
            'compression_ratio': (original_length - len(text)) / original_length if original_length > 0 else 0
        }
    
    def clean_page_content(self, pages_content: List[str]) -> List[Dict]:
        """تنظيف محتوى صفحات متعددة"""
        cleaned_pages = []
        
        for i, page_content in enumerate(pages_content):
            result = self.clean_content(page_content)
            result['page_number'] = i + 1
            cleaned_pages.append(result)
        
        return cleaned_pages
    
    def get_cleaning_statistics(self, cleaned_pages: List[Dict]) -> Dict:
        """إحصائيات عملية التنظيف"""
        total_pages = len(cleaned_pages)
        useful_pages = sum(1 for page in cleaned_pages if page['is_useful'])
        total_original_length = sum(page['original_length'] for page in cleaned_pages)
        total_cleaned_length = sum(page['cleaned_length'] for page in cleaned_pages)
        
        # تجميع التحسينات
        all_improvements = []
        for page in cleaned_pages:
            all_improvements.extend(page['improvements'])
        
        improvement_counts = {}
        for improvement in all_improvements:
            improvement_counts[improvement] = improvement_counts.get(improvement, 0) + 1
        
        return {
            'total_pages': total_pages,
            'useful_pages': useful_pages,
            'useless_pages': total_pages - useful_pages,
            'total_original_length': total_original_length,
            'total_cleaned_length': total_cleaned_length,
            'total_compression_ratio': (total_original_length - total_cleaned_length) / total_original_length if total_original_length > 0 else 0,
            'improvement_counts': improvement_counts,
            'useful_pages_ratio': useful_pages / total_pages if total_pages > 0 else 0
        }

# إنشاء مثيل عام للاستخدام
content_cleaner = ContentCleaner()
