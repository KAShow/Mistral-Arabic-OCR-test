"""
محسن الفهرسة للوثائق القانونية
يوفر فهرسة هيكلية ومتقدمة للوثائق القانونية العربية
"""

import re
from typing import List, Dict, Optional, Tuple, Set
from collections import Counter, defaultdict

class LegalIndexer:
    """مفهرس متخصص للوثائق القانونية"""
    
    def __init__(self):
        """تهيئة المفهرس القانوني"""
        # المصطلحات القانونية المهمة
        self.legal_terms = {
            # المصطلحات الأساسية
            'أساسي': ['قانون', 'مرسوم', 'نظام', 'لائحة', 'دستور', 'ميثاق'],
            
            # مصطلحات العمل والعمال
            'عمل': ['عامل', 'صاحب العمل', 'عقد العمل', 'أجر', 'راتب', 'مكافأة', 'إجازة', 'تأمين'],
            
            # المصطلحات الإجرائية
            'إجراءات': ['محكمة', 'دعوى', 'استئناف', 'تحكيم', 'تظلم', 'طعن', 'حكم', 'قضاء'],
            
            # العقوبات والجزاءات
            'عقوبات': ['غرامة', 'حبس', 'سجن', 'إنذار', 'فصل', 'جزاء', 'عقوبة', 'مخالفة'],
            
            # الحقوق والواجبات
            'حقوق': ['حق', 'واجب', 'التزام', 'مسؤولية', 'ضمان', 'حماية', 'رعاية'],
            
            # الزمن والمواعيد
            'زمنية': ['يوم', 'شهر', 'سنة', 'مدة', 'فترة', 'موعد', 'تاريخ', 'مهلة'],
            
            # المالية
            'مالية': ['دينار', 'ريال', 'درهم', 'مبلغ', 'تعويض', 'رسوم', 'ضريبة', 'استحقاق']
        }
        
        # كلمات الوقف القانونية (أكثر تخصصاً)
        self.legal_stop_words = {
            'في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك',
            'التي', 'الذي', 'اللذان', 'اللتان', 'اللذين', 'اللتين', 'اللواتي',
            'أن', 'إن', 'كان', 'كانت', 'يكون', 'تكون', 'سوف', 'قد', 'لقد',
            'ما', 'لا', 'ليس', 'غير', 'سوى', 'بل', 'لكن', 'إلا', 'حتى',
            'أو', 'أم', 'إما', 'كل', 'بعض', 'جميع', 'كلا', 'كلتا',
            'هو', 'هي', 'هم', 'هن', 'أنت', 'أنتم', 'أنتن', 'أنا', 'نحن',
            'له', 'لها', 'لهم', 'لهن', 'بك', 'بها', 'بهم', 'بهن',
            'يجب', 'يجوز', 'ينبغي', 'يمكن', 'يحق', 'يحظر', 'يعتبر', 'يقصد'
        }
        
        # أنماط الهيكل القانوني
        self.structure_patterns = {
            'باب': r'الباب\s+(?:الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\w+)',
            'فصل': r'الفصل\s+(?:الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\w+)',
            'مادة': r'المادة\s*\(?\s*(\d+)\s*\)?',
            'فقرة': r'الفقرة\s*\(?\s*([أ-ي]|\d+)\s*\)?',
            'بند': r'البند\s*\(?\s*(\d+)\s*\)?'
        }
        
        # أنماط الأرقام والتواريخ
        self.number_patterns = {
            'سنة': r'(?:لسنة|عام)\s+(\d{4})',
            'رقم_قانون': r'رقم\s*\(?\s*(\d+)\s*\)?',
            'تاريخ': r'(\d{1,2})/(\d{1,2})/(\d{4})',
            'مبلغ': r'(\d+(?:\.\d+)?)\s*(?:دينار|ريال|درهم)',
            'نسبة': r'(\d+(?:\.\d+)?)\s*%'
        }
    
    def extract_legal_structure(self, text: str) -> Dict[str, List]:
        """استخراج الهيكل القانوني من النص"""
        structure = defaultdict(list)
        
        for structure_type, pattern in self.structure_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                item = {
                    'type': structure_type,
                    'text': match.group(0),
                    'position': match.start(),
                    'number': match.group(1) if match.groups() else None
                }
                structure[structure_type].append(item)
        
        return dict(structure)
    
    def extract_legal_numbers(self, text: str) -> Dict[str, List]:
        """استخراج الأرقام والتواريخ القانونية"""
        numbers = defaultdict(list)
        
        for number_type, pattern in self.number_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                item = {
                    'type': number_type,
                    'value': match.group(1) if match.groups() else match.group(0),
                    'full_match': match.group(0),
                    'position': match.start()
                }
                numbers[number_type].append(item)
        
        return dict(numbers)
    
    def categorize_legal_terms(self, words: List[str]) -> Dict[str, List[str]]:
        """تصنيف الكلمات حسب المجالات القانونية"""
        categorized = defaultdict(list)
        
        for word in words:
            word_lower = word.lower()
            for category, terms in self.legal_terms.items():
                if any(term in word_lower for term in terms):
                    categorized[category].append(word)
                    break
            else:
                # إذا لم تندرج تحت أي فئة، ضعها في "عام"
                if len(word) > 3 and word_lower not in self.legal_stop_words:
                    categorized['عام'].append(word)
        
        return dict(categorized)
    
    def clean_text_simple(self, text: str) -> Dict:
        """تنظيف بسيط للنص"""
        if not text or len(text.strip()) < 20:
            return {'cleaned_text': '', 'is_useful': False}
        
        # إزالة الأسطر الفارغة والمسافات الزائدة
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        return {'cleaned_text': cleaned, 'is_useful': len(cleaned) > 20}
    
    def extract_enhanced_keywords(self, text: str, max_keywords: int = 30) -> Dict:
        """استخراج كلمات مفتاحية محسنة للنصوص القانونية"""
        # تنظيف النص
        cleaned_result = self.clean_text_simple(text)
        if not cleaned_result['is_useful']:
            return {'keywords': [], 'categories': {}, 'confidence': 0}
        
        cleaned_text = cleaned_result['cleaned_text']
        
        # استخراج الكلمات
        words = re.findall(r'[\u0600-\u06FF\u0750-\u077F]+', cleaned_text)
        
        # تصفية كلمات الوقف
        filtered_words = [
            word for word in words 
            if len(word) > 2 and word.lower() not in self.legal_stop_words
        ]
        
        # حساب التكرار
        word_freq = Counter(filtered_words)
        
        # الحصول على أهم الكلمات
        top_words = [word for word, freq in word_freq.most_common(max_keywords)]
        
        # تصنيف الكلمات
        categories = self.categorize_legal_terms(top_words)
        
        # حساب درجة الثقة
        confidence = self.calculate_keyword_confidence(top_words, categories)
        
        return {
            'keywords': top_words,
            'categories': categories,
            'word_frequencies': dict(word_freq.most_common(max_keywords)),
            'confidence': confidence
        }
    
    def calculate_keyword_confidence(self, keywords: List[str], categories: Dict) -> float:
        """حساب درجة ثقة الكلمات المفتاحية"""
        if not keywords:
            return 0.0
        
        # نقاط للفئات المختلفة
        category_scores = {
            'أساسي': 0.3,
            'عمل': 0.2,
            'إجراءات': 0.2,
            'عقوبات': 0.15,
            'حقوق': 0.1,
            'زمنية': 0.05,
            'مالية': 0.1,
            'عام': 0.02
        }
        
        total_score = 0
        total_words = len(keywords)
        
        for category, words in categories.items():
            category_weight = category_scores.get(category, 0.01)
            category_contribution = (len(words) / total_words) * category_weight
            total_score += category_contribution
        
        return min(total_score, 1.0)
    
    def create_legal_chunks(self, text: str, chunk_size: int = 500) -> List[Dict]:
        """تقسيم النص إلى أجزاء قانونية منطقية"""
        # تنظيف النص
        cleaned_result = self.clean_text_simple(text)
        if not cleaned_result['is_useful']:
            return []
        
        cleaned_text = cleaned_result['cleaned_text']
        
        # استخراج الهيكل القانوني
        structure = self.extract_legal_structure(cleaned_text)
        
        chunks = []
        
        # إذا وجدنا مواد قانونية، نقسم حسبها
        if 'مادة' in structure and len(structure['مادة']) > 1:
            chunks = self.chunk_by_articles(cleaned_text, structure['مادة'])
        else:
            # تقسيم عادي بالفقرات
            chunks = self.chunk_by_paragraphs(cleaned_text, chunk_size)
        
        # إضافة معلومات إضافية لكل جزء
        enhanced_chunks = []
        for i, chunk in enumerate(chunks):
            keywords_result = self.extract_enhanced_keywords(chunk['content'], 15)
            numbers = self.extract_legal_numbers(chunk['content'])
            
            enhanced_chunk = {
                **chunk,
                'chunk_id': i,
                'keywords': keywords_result['keywords'],
                'keyword_categories': keywords_result['categories'],
                'legal_numbers': numbers,
                'confidence': keywords_result['confidence']
            }
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def chunk_by_articles(self, text: str, articles: List[Dict]) -> List[Dict]:
        """تقسيم النص حسب المواد القانونية"""
        chunks = []
        
        # ترتيب المواد حسب الموقع
        sorted_articles = sorted(articles, key=lambda x: x['position'])
        
        for i, article in enumerate(sorted_articles):
            start_pos = article['position']
            end_pos = sorted_articles[i + 1]['position'] if i + 1 < len(sorted_articles) else len(text)
            
            content = text[start_pos:end_pos].strip()
            
            if len(content) > 50:  # تجاهل المواد الفارغة أو القصيرة جداً
                chunks.append({
                    'content': content,
                    'type': 'article',
                    'article_number': article['number'],
                    'position': i,
                    'start_char': start_pos,
                    'end_char': end_pos,
                    'length': len(content)
                })
        
        return chunks
    
    def chunk_by_paragraphs(self, text: str, chunk_size: int) -> List[Dict]:
        """تقسيم النص حسب الفقرات"""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        chunk_position = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            if len(current_chunk + paragraph) > chunk_size and current_chunk:
                # حفظ الجزء الحالي
                chunks.append({
                    'content': current_chunk.strip(),
                    'type': 'paragraph_group',
                    'position': chunk_position,
                    'length': len(current_chunk)
                })
                chunk_position += 1
                current_chunk = paragraph + '\n\n'
            else:
                current_chunk += paragraph + '\n\n'
        
        # حفظ الجزء الأخير
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'type': 'paragraph_group',
                'position': chunk_position,
                'length': len(current_chunk)
            })
        
        return chunks
    
    def create_comprehensive_index(self, text: str, document_id: str = None) -> Dict:
        """إنشاء فهرس شامل للوثيقة القانونية"""
        # الفهرسة الأساسية
        keywords_result = self.extract_enhanced_keywords(text, 50)
        
        # الهيكل القانوني
        structure = self.extract_legal_structure(text)
        
        # الأرقام والتواريخ
        numbers = self.extract_legal_numbers(text)
        
        # التقسيم المحسن
        chunks = self.create_legal_chunks(text)
        
        # إحصائيات
        stats = {
            'total_words': len(re.findall(r'[\u0600-\u06FF\u0750-\u077F]+', text)),
            'total_chars': len(text),
            'articles_count': len(structure.get('مادة', [])),
            'chapters_count': len(structure.get('فصل', [])),
            'sections_count': len(structure.get('باب', [])),
            'chunks_count': len(chunks),
            'legal_numbers_count': sum(len(nums) for nums in numbers.values())
        }
        
        return {
            'document_id': document_id,
            'keywords': keywords_result['keywords'],
            'keyword_categories': keywords_result['categories'],
            'legal_structure': structure,
            'legal_numbers': numbers,
            'chunks': chunks,
            'statistics': stats,
            'overall_confidence': keywords_result['confidence']
        }

# إنشاء مثيل عام للاستخدام
legal_indexer = LegalIndexer()
