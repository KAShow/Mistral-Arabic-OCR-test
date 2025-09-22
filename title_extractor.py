"""
مستخرج العناوين الذكي للوثائق القانونية
يستخرج العناوين الحقيقية من المحتوى بدلاً من أسماء الملفات
"""

import re
from typing import List, Dict, Optional, Tuple
from content_cleaner import content_cleaner

class TitleExtractor:
    """مستخرج العناوين الذكي للوثائق القانونية"""
    
    def __init__(self):
        """تهيئة مستخرج العناوين"""
        # الكلمات المفتاحية للوثائق القانونية
        self.legal_keywords = [
            'قانون', 'مرسوم', 'نظام', 'لائحة', 'قرار', 'تعليمات',
            'دستور', 'اتفاقية', 'معاهدة', 'بروتوكول', 'ميثاق'
        ]
        
        # أنماط العناوين القانونية
        self.title_patterns = [
            # قانون رقم (X) لسنة YYYY
            r'قانون\s+رقم\s*\(\s*\d+\s*\)\s+لسنة\s+\d{4}.*?(?:\n|$)',
            # مرسوم بقانون رقم (X) لسنة YYYY
            r'مرسوم\s+بقانون\s+رقم\s*\(\s*\d+\s*\)\s+لسنة\s+\d{4}.*?(?:\n|$)',
            # نظام رقم (X) لعام YYYY
            r'نظام\s+رقم\s*\(\s*\d+\s*\)\s+لعام\s+\d{4}.*?(?:\n|$)',
            # أي عنوان يبدأ بالكلمات المفتاحية
            r'(?:' + '|'.join(self.legal_keywords) + r')\s+[^\n]{10,100}',
        ]
        
        # أنماط العناوين الفرعية
        self.subtitle_patterns = [
            r'بإصدار\s+[^\n]{10,80}',  # بإصدار قانون العمل
            r'بشأن\s+[^\n]{10,80}',    # بشأن تنظيم العمل
            r'في\s+[^\n]{10,80}',      # في القطاع الأهلي
        ]
        
        # كلمات يجب تجاهلها في العناوين
        self.ignore_words = [
            'img-', 'jpeg', 'png', 'gif', 'صورة', 'الصفحة',
            'فارغة', 'لا يوجد', 'غير واضح'
        ]
    
    def is_useful_page(self, page_content: str) -> bool:
        """تحديد ما إذا كانت الصفحة مفيدة لاستخراج العنوان"""
        if not page_content or len(page_content.strip()) < 20:
            return False
        
        # فحص وجود مؤشرات عدم الفائدة
        content_lower = page_content.lower()
        for ignore_word in self.ignore_words:
            if ignore_word in content_lower:
                return False
        
        # فحص وجود نص عربي حقيقي
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', page_content))
        if arabic_chars < 10:
            return False
        
        return True
    
    def limit_title_words(self, title: str, max_words: int = 10) -> str:
        """تحديد طول العنوان بعدد كلمات معين"""
        if not title:
            return title
        
        words = title.split()
        if len(words) <= max_words:
            return title
        
        # أخذ أول max_words كلمات
        limited_title = ' '.join(words[:max_words])
        
        # إضافة نقاط إذا تم اقتطاع العنوان
        if len(words) > max_words:
            limited_title += "..."
        
        return limited_title
    
    def extract_title_from_text(self, text: str) -> Optional[Dict]:
        """استخراج العنوان من نص واحد"""
        if not text or not self.is_useful_page(text):
            return None
        
        # تنظيف النص أولاً
        cleaned_result = content_cleaner.clean_content(text)
        if not cleaned_result['is_useful']:
            return None
        
        cleaned_text = cleaned_result['cleaned_text']
        
        # البحث عن العناوين الرئيسية
        for pattern in self.title_patterns:
            matches = re.findall(pattern, cleaned_text, re.MULTILINE | re.IGNORECASE)
            if matches:
                title = matches[0].strip()
                # تحديد طول العنوان
                title = self.limit_title_words(title, 10)
                
                # البحث عن عنوان فرعي
                subtitle = self.extract_subtitle(cleaned_text, title)
                if subtitle:
                    subtitle = self.limit_title_words(subtitle, 6)  # عنوان فرعي أقصر
                
                # تكوين العنوان الكامل مع مراعاة الحد الأقصى
                if subtitle:
                    full_title = f"{title} - {subtitle}"
                    full_title = self.limit_title_words(full_title, 10)
                else:
                    full_title = title
                
                return {
                    'title': title,
                    'subtitle': subtitle,
                    'full_title': full_title,
                    'confidence': 0.9,
                    'source': 'pattern_match'
                }
        
        # إذا لم نجد عنواناً بالأنماط، نبحث عن أول سطر مفيد
        fallback_title = self.extract_fallback_title(cleaned_text)
        if fallback_title:
            fallback_title = self.limit_title_words(fallback_title, 10)
            return {
                'title': fallback_title,
                'subtitle': None,
                'full_title': fallback_title,
                'confidence': 0.5,
                'source': 'fallback'
            }
        
        return None
    
    def extract_subtitle(self, text: str, main_title: str) -> Optional[str]:
        """استخراج العنوان الفرعي"""
        # البحث بعد العنوان الرئيسي
        title_index = text.find(main_title)
        if title_index == -1:
            return None
        
        remaining_text = text[title_index + len(main_title):]
        
        for pattern in self.subtitle_patterns:
            matches = re.findall(pattern, remaining_text, re.MULTILINE | re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return None
    
    def extract_fallback_title(self, text: str) -> Optional[str]:
        """استخراج عنوان احتياطي من أول سطر مفيد"""
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if len(line) < 10 or len(line) > 200:
                continue
            
            # تجاهل الأسطر التي تحتوي على كلمات يجب تجاهلها
            line_lower = line.lower()
            if any(ignore_word in line_lower for ignore_word in self.ignore_words):
                continue
            
            # فحص وجود نص عربي كافي
            arabic_chars = len(re.findall(r'[\u0600-\u06FF]', line))
            if arabic_chars < 5:
                continue
            
            # تنظيف السطر
            cleaned_line = re.sub(r'[^\w\s\u0600-\u06FF\(\)\-\d]', '', line)
            if len(cleaned_line.strip()) >= 10:
                return cleaned_line.strip()
        
        return None
    
    def extract_title_from_pages(self, pages_content: List[str]) -> Dict:
        """استخراج العنوان من صفحات متعددة"""
        if not pages_content:
            return {
                'title': None,
                'subtitle': None,
                'full_title': None,
                'confidence': 0,
                'source': 'no_content',
                'page_used': None,
                'alternatives': []
            }
        
        alternatives = []
        best_result = None
        
        # البحث في أول 3 صفحات مفيدة
        useful_pages = []
        for i, page_content in enumerate(pages_content[:5]):  # فحص أول 5 صفحات
            if self.is_useful_page(page_content):
                useful_pages.append((i + 1, page_content))
                if len(useful_pages) >= 3:
                    break
        
        if not useful_pages:
            return {
                'title': None,
                'subtitle': None,
                'full_title': None,
                'confidence': 0,
                'source': 'no_useful_pages',
                'page_used': None,
                'alternatives': []
            }
        
        # استخراج العناوين من الصفحات المفيدة
        for page_num, page_content in useful_pages:
            result = self.extract_title_from_text(page_content)
            if result:
                result['page_used'] = page_num
                alternatives.append(result)
                
                # اختيار أفضل نتيجة
                if not best_result or result['confidence'] > best_result['confidence']:
                    best_result = result
        
        if best_result:
            best_result['alternatives'] = [alt for alt in alternatives if alt != best_result]
            return best_result
        
        # إذا لم نجد أي عنوان، نستخدم اسم الملف كاحتياط
        return {
            'title': None,
            'subtitle': None,
            'full_title': None,
            'confidence': 0,
            'source': 'no_title_found',
            'page_used': None,
            'alternatives': alternatives
        }
    
    def extract_document_type(self, title: str) -> str:
        """استخراج نوع الوثيقة من العنوان"""
        if not title:
            return 'غير محدد'
        
        title_lower = title.lower()
        
        type_mapping = {
            'قانون': 'قانون',
            'مرسوم': 'مرسوم',
            'نظام': 'نظام',
            'لائحة': 'لائحة',
            'قرار': 'قرار',
            'تعليمات': 'تعليمات',
            'دستور': 'دستور',
            'اتفاقية': 'اتفاقية',
            'معاهدة': 'معاهدة',
            'بروتوكول': 'بروتوكول',
            'ميثاق': 'ميثاق'
        }
        
        for keyword, doc_type in type_mapping.items():
            if keyword in title_lower:
                return doc_type
        
        return 'وثيقة قانونية'
    
    def calculate_title_quality_score(self, title_result: Dict) -> float:
        """حساب درجة جودة العنوان المستخرج"""
        if not title_result or not title_result.get('title'):
            return 0.0
        
        score = title_result.get('confidence', 0)
        title = title_result['title']
        
        # إضافة نقاط للخصائص الجيدة
        if any(keyword in title.lower() for keyword in self.legal_keywords):
            score += 0.2
        
        if re.search(r'رقم\s*\(\s*\d+\s*\)', title):  # يحتوي على رقم
            score += 0.1
        
        if re.search(r'لسنة\s+\d{4}', title):  # يحتوي على سنة
            score += 0.1
        
        if 20 <= len(title) <= 100:  # طول مناسب
            score += 0.1
        
        if title_result.get('subtitle'):  # يحتوي على عنوان فرعي
            score += 0.1
        
        return min(score, 1.0)

# إنشاء مثيل عام للاستخدام
title_extractor = TitleExtractor()
