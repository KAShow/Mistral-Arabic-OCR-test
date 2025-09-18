#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محرك البحث القانوني المحسن مع دعم عرض الصفحات الكاملة
"""

import sqlite3
import re
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json

@dataclass
class PageContent:
    """كلاس لتمثيل محتوى صفحة كاملة"""
    page_number: int
    content: str
    document_name: str

class EnhancedLegalSearchEngine:
    """محرك البحث القانوني المحسن"""
    
    def __init__(self, db_path: str = "enhanced_legal_database.db"):
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """إنشاء قاعدة البيانات والجداول المحسنة"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # إنشاء جدول الوثائق
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            title TEXT,
            file_path TEXT,
            pages_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # إنشاء جدول الصفحات الكاملة (جديد)
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            page_number INTEGER,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (id),
            UNIQUE(document_id, page_number)
        )
        ''')
        
        # إنشاء جدول المواد القانونية (محسن)
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            page_id INTEGER,
            page_number INTEGER,
            chapter TEXT,
            section TEXT,
            article_number TEXT,
            title TEXT,
            content TEXT,
            article_type TEXT,
            position_in_page INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (id),
            FOREIGN KEY (page_id) REFERENCES pages (id)
        )
        ''')
        
        # إنشاء جدول FTS5 للبحث النصي السريع
        self.conn.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
            article_id,
            document_name,
            page_number,
            chapter,
            section,
            article_number,
            title,
            content,
            content=articles,
            content_rowid=id
        )
        ''')
        
        # إنشاء جدول FTS5 للصفحات الكاملة (جديد)
        self.conn.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
            page_id,
            document_name,
            page_number,
            content,
            content=pages,
            content_rowid=id
        )
        ''')
        
        # Triggers للتحديث التلقائي
        self._create_triggers()
        
        self.conn.commit()
        print(" تم إنشاء قاعدة البيانات المحسنة بنجاح!")

    def _create_triggers(self):
        """إنشاء triggers للتحديث التلقائي لجداول FTS"""
        
        # Triggers للمواد
        self.conn.execute('''
        CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
            INSERT INTO articles_fts(article_id, document_name, page_number, chapter, section, article_number, title, content)
            VALUES (new.id, (SELECT name FROM documents WHERE id = new.document_id), 
                   new.page_number, new.chapter, new.section, new.article_number, new.title, new.content);
        END
        ''')
        
        self.conn.execute('''
        CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
            DELETE FROM articles_fts WHERE article_id = old.id;
        END
        ''')
        
        # Triggers للصفحات
        self.conn.execute('''
        CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
            INSERT INTO pages_fts(page_id, document_name, page_number, content)
            VALUES (new.id, (SELECT name FROM documents WHERE id = new.document_id), 
                   new.page_number, new.content);
        END
        ''')
        
        self.conn.execute('''
        CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
            DELETE FROM pages_fts WHERE page_id = old.id;
        END
        ''')

    def parse_markdown_document_enhanced(self, file_path: str, document_name: str) -> Tuple[List[PageContent], List]:
        """تحليل محسن للوثيقة مع حفظ الصفحات الكاملة"""
        pages_content = []
        articles = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # تقسيم المحتوى حسب الصفحات
        page_sections = re.split(r'^## Page (\d+)', content, flags=re.MULTILINE)
        
        current_chapter = ""
        current_section = ""
        article_id = 0
        
        for i in range(1, len(page_sections), 2):
            page_num = int(page_sections[i])
            page_content = page_sections[i + 1].strip()
            
            # حفظ محتوى الصفحة الكاملة
            pages_content.append(PageContent(
                page_number=page_num,
                content=page_content,
                document_name=document_name
            ))
            
            # تحليل محتوى الصفحة للمواد القانونية
            lines = page_content.split('\n')
            current_article_content = []
            current_article_number = ""
            current_article_title = ""
            in_article = False
            position_in_page = 0
            
            for line_idx, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # تحديد الباب
                if line.startswith('الباب'):
                    current_chapter = line
                    continue
                
                # تحديد الفصل
                if line.startswith('الفصل'):
                    current_section = line
                    continue
                
                # تحديد المادة
                article_match = re.match(r'^(?:\*\*)?المادة \(([^)]+)\)(?:\*\*)?', line)
                if article_match:
                    # حفظ المادة السابقة إذا كانت موجودة
                    if in_article and current_article_content:
                        article_id += 1
                        articles.append({
                            'id': article_id,
                            'document_name': document_name,
                            'page_number': page_num,
                            'chapter': current_chapter,
                            'section': current_section,
                            'article_number': current_article_number,
                            'title': current_article_title,
                            'content': '\n'.join(current_article_content),
                            'article_type': 'article',
                            'position_in_page': position_in_page
                        })
                    
                    # بداية مادة جديدة
                    current_article_number = article_match.group(1)
                    current_article_title = ""
                    current_article_content = []
                    in_article = True
                    position_in_page = line_idx
                    continue
                
                # محتوى المادة
                if in_article:
                    current_article_content.append(line)
                else:
                    # محتوى عام
                    if line and len(line) > 10:
                        article_id += 1
                        articles.append({
                            'id': article_id,
                            'document_name': document_name,
                            'page_number': page_num,
                            'chapter': current_chapter,
                            'section': current_section,
                            'article_number': "",
                            'title': "",
                            'content': line,
                            'article_type': 'general',
                            'position_in_page': line_idx
                        })
            
            # حفظ المادة الأخيرة في الصفحة
            if in_article and current_article_content:
                article_id += 1
                articles.append({
                    'id': article_id,
                    'document_name': document_name,
                    'page_number': page_num,
                    'chapter': current_chapter,
                    'section': current_section,
                    'article_number': current_article_number,
                    'title': current_article_title,
                    'content': '\n'.join(current_article_content),
                    'article_type': 'article',
                    'position_in_page': position_in_page
                })
        
        print(f" تم استخراج {len(pages_content)} صفحة و {len(articles)} عنصر من الوثيقة")
        return pages_content, articles

    def index_document_enhanced(self, file_path: str, document_name: str, title: str = ""):
        """فهرسة محسنة للوثيقة مع حفظ الصفحات الكاملة"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"الملف غير موجود: {file_path}")
        
        # إضافة الوثيقة
        cursor = self.conn.execute('''
        INSERT OR REPLACE INTO documents (name, title, file_path, pages_count)
        VALUES (?, ?, ?, ?)
        ''', (document_name, title, file_path, 0))
        
        document_id = cursor.lastrowid
        
        # حذف البيانات القديمة
        self.conn.execute('DELETE FROM articles WHERE document_id = ?', (document_id,))
        self.conn.execute('DELETE FROM pages WHERE document_id = ?', (document_id,))
        
        # تحليل وفهرسة المحتوى
        pages_content, articles = self.parse_markdown_document_enhanced(file_path, document_name)
        
        # إدراج الصفحات الكاملة
        page_ids = {}
        for page in pages_content:
            cursor = self.conn.execute('''
            INSERT INTO pages (document_id, page_number, content)
            VALUES (?, ?, ?)
            ''', (document_id, page.page_number, page.content))
            page_ids[page.page_number] = cursor.lastrowid
        
        # إدراج المواد مع ربطها بالصفحات
        for article in articles:
            page_id = page_ids.get(article['page_number'])
            self.conn.execute('''
            INSERT INTO articles 
            (document_id, page_id, page_number, chapter, section, article_number, 
             title, content, article_type, position_in_page)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                document_id, page_id, article['page_number'], article['chapter'], 
                article['section'], article['article_number'], article['title'], 
                article['content'], article['article_type'], article['position_in_page']
            ))
        
        # تحديث عدد الصفحات
        max_page = max([p.page_number for p in pages_content]) if pages_content else 0
        self.conn.execute('UPDATE documents SET pages_count = ? WHERE id = ?', (max_page, document_id))
        
        self.conn.commit()
        print(f" تم فهرسة الوثيقة '{document_name}' بنجاح!")
        return len(articles)

    def get_page_content(self, document_name: str, page_number: int) -> Optional[Dict]:
        """الحصول على محتوى صفحة كاملة"""
        cursor = self.conn.execute('''
        SELECT p.id, p.page_number, p.content, d.name as document_name, d.title as document_title
        FROM pages p
        JOIN documents d ON p.document_id = d.id
        WHERE d.name = ? AND p.page_number = ?
        ''', (document_name, page_number))
        
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_page_with_highlighted_text(self, document_name: str, page_number: int, search_query: str = "") -> Optional[Dict]:
        """الحصول على صفحة مع تمييز النص المطلوب"""
        page_data = self.get_page_content(document_name, page_number)
        
        if not page_data:
            return None
        
        # تمييز النص إذا كان هناك استعلام بحث
        if search_query:
            highlighted_content = self._highlight_matches(page_data['content'], search_query)
            page_data['highlighted_content'] = highlighted_content
        else:
            page_data['highlighted_content'] = page_data['content']
        
        return page_data

    def _highlight_matches(self, text: str, query: str) -> str:
        """تمييز الكلمات المطابقة في النص"""
        words = query.split()
        highlighted_text = text
        
        for word in words:
            if len(word) > 2:  # تجنب الكلمات القصيرة جداً
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                highlighted_text = pattern.sub(f'<mark class="highlight">{word}</mark>', highlighted_text)
        
        return highlighted_text

    def search_enhanced(self, query: str, limit: int = 10) -> List[Dict]:
        """بحث محسن مع معلومات إضافية"""
        # البحث في المواد
        cursor = self.conn.execute('''
        SELECT 
            a.id, a.document_id, a.page_id,
            d.name as document_name, d.title as document_title,
            a.page_number, a.chapter, a.section, a.article_number,
            a.title, a.content, a.article_type, a.position_in_page,
            articles_fts.rank
        FROM articles_fts 
        JOIN articles a ON articles_fts.rowid = a.id
        JOIN documents d ON a.document_id = d.id
        WHERE articles_fts MATCH ?
        ORDER BY articles_fts.rank
        LIMIT ?
        ''', (query, limit))
        
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result['highlighted_content'] = self._highlight_matches(result['content'], query)
            results.append(result)
        
        return results

    def get_statistics(self) -> Dict:
        """إحصائيات قاعدة البيانات المحسنة"""
        stats = {}
        
        # عدد الوثائق
        cursor = self.conn.execute('SELECT COUNT(*) FROM documents')
        stats['documents_count'] = cursor.fetchone()[0]
        
        # عدد الصفحات
        cursor = self.conn.execute('SELECT COUNT(*) FROM pages')
        stats['pages_count'] = cursor.fetchone()[0]
        
        # عدد المواد
        cursor = self.conn.execute('SELECT COUNT(*) FROM articles')
        stats['articles_count'] = cursor.fetchone()[0]
        
        # عدد المواد حسب النوع
        cursor = self.conn.execute('''
        SELECT article_type, COUNT(*) 
        FROM articles 
        GROUP BY article_type
        ''')
        stats['articles_by_type'] = dict(cursor.fetchall())
        
        return stats

    def get_all_documents(self):
        """جلب جميع الوثائق من قاعدة البيانات"""
        cursor = self.conn.execute('''
        SELECT id, name, title, file_path, pages_count, created_at
        FROM documents
        ORDER BY created_at DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

    def get_sample_articles(self, limit: int = 10):
        """جلب عينة من المواد القانونية"""
        cursor = self.conn.execute('''
        SELECT 
            a.id, a.article_number, a.title, a.content,
            a.article_type, a.page_number,
            d.name as document_name
        FROM articles a
        JOIN documents d ON a.document_id = d.id
        ORDER BY a.id DESC
        LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    print(" نظام البحث القانوني المحسن")
    print("=" * 50)
    
    # إنشاء محرك البحث المحسن
    engine = EnhancedLegalSearchEngine()
    
    # فهرسة وثيقة قانون العمل
    document_path = "docs_exports/document.md"
    if os.path.exists(document_path):
        engine.index_document_enhanced(
            document_path, 
            "قانون العمل في القطاع الأهلي", 
            "قانون رقم (36) لسنة 2012"
        )
        
        # عرض الإحصائيات
        stats = engine.get_statistics()
        print(f"\n الإحصائيات المحسنة:")
        print(f"    الوثائق: {stats['documents_count']}")
        print(f"    الصفحات: {stats['pages_count']}")
        print(f"    المواد: {stats['articles_count']}")
        print(f"    تفصيل: {stats['articles_by_type']}")
        
        # اختبار عرض الصفحة الكاملة
        print(f"\n اختبار عرض الصفحة الكاملة:")
        page_data = engine.get_page_with_highlighted_text("قانون العمل في القطاع الأهلي", 3, "العامل")
        if page_data:
            print(f" تم العثور على الصفحة {page_data['page_number']}")
            print(f" المحتوى: {len(page_data['content'])} حرف")
        
    else:
        print(" لم يتم العثور على ملف الوثيقة!")
    
    engine.close()
