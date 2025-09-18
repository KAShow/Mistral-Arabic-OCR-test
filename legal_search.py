#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام فهرسة وبحث القوانين البحرينية
باستخدام SQLite مع Full-Text Search (FTS5)
"""

import sqlite3
import re
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json

@dataclass
class LegalArticle:
    """كلاس لتمثيل مادة قانونية"""
    id: int
    document_name: str
    page_number: int
    chapter: str
    section: str
    article_number: str
    title: str
    content: str
    article_type: str  # 'article', 'definition', 'general'

class LegalSearchEngine:
    """محرك البحث القانوني"""
    
    def __init__(self, db_path: str = "legal_database.db"):
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """إنشاء قاعدة البيانات والجداول"""
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
        
        # إنشاء جدول المواد القانونية
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            page_number INTEGER,
            chapter TEXT,
            section TEXT,
            article_number TEXT,
            title TEXT,
            content TEXT,
            article_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
        ''')
        
        # إنشاء جدول FTS5 للبحث النصي السريع
        self.conn.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
            article_id,
            document_name,
            chapter,
            section,
            article_number,
            title,
            content,
            content=articles,
            content_rowid=id
        )
        ''')
        
        # إنشاء triggers للتحديث التلقائي لجدول FTS
        self.conn.execute('''
        CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
            INSERT INTO articles_fts(article_id, document_name, chapter, section, article_number, title, content)
            VALUES (new.id, (SELECT name FROM documents WHERE id = new.document_id), 
                   new.chapter, new.section, new.article_number, new.title, new.content);
        END
        ''')
        
        self.conn.execute('''
        CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
            DELETE FROM articles_fts WHERE article_id = old.id;
        END
        ''')
        
        self.conn.execute('''
        CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
            DELETE FROM articles_fts WHERE article_id = old.id;
            INSERT INTO articles_fts(article_id, document_name, chapter, section, article_number, title, content)
            VALUES (new.id, (SELECT name FROM documents WHERE id = new.document_id), 
                   new.chapter, new.section, new.article_number, new.title, new.content);
        END
        ''')
        
        self.conn.commit()
        print("✅ تم إنشاء قاعدة البيانات بنجاح!")

    def parse_markdown_document(self, file_path: str, document_name: str) -> List[LegalArticle]:
        """تحليل وثيقة Markdown واستخراج المواد القانونية"""
        articles = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # تقسيم المحتوى حسب الصفحات
        pages = re.split(r'^## Page (\d+)', content, flags=re.MULTILINE)
        
        current_chapter = ""
        current_section = ""
        article_id = 0
        
        for i in range(1, len(pages), 2):
            page_num = int(pages[i])
            page_content = pages[i + 1].strip()
            
            # تحليل محتوى الصفحة
            lines = page_content.split('\n')
            current_article_content = []
            current_article_number = ""
            current_article_title = ""
            in_article = False
            
            for line in lines:
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
                        articles.append(LegalArticle(
                            id=article_id,
                            document_name=document_name,
                            page_number=page_num,
                            chapter=current_chapter,
                            section=current_section,
                            article_number=current_article_number,
                            title=current_article_title,
                            content='\n'.join(current_article_content),
                            article_type='article'
                        ))
                    
                    # بداية مادة جديدة
                    current_article_number = article_match.group(1)
                    current_article_title = ""
                    current_article_content = []
                    in_article = True
                    continue
                
                # محتوى المادة
                if in_article:
                    current_article_content.append(line)
                else:
                    # محتوى عام (مقدمة، خاتمة، إلخ)
                    if line and len(line) > 10:
                        article_id += 1
                        articles.append(LegalArticle(
                            id=article_id,
                            document_name=document_name,
                            page_number=page_num,
                            chapter=current_chapter,
                            section=current_section,
                            article_number="",
                            title="",
                            content=line,
                            article_type='general'
                        ))
            
            # حفظ المادة الأخيرة في الصفحة
            if in_article and current_article_content:
                article_id += 1
                articles.append(LegalArticle(
                    id=article_id,
                    document_name=document_name,
                    page_number=page_num,
                    chapter=current_chapter,
                    section=current_section,
                    article_number=current_article_number,
                    title=current_article_title,
                    content='\n'.join(current_article_content),
                    article_type='article'
                ))
        
        print(f"✅ تم استخراج {len(articles)} عنصر من الوثيقة")
        return articles

    def index_document(self, file_path: str, document_name: str, title: str = ""):
        """فهرسة وثيقة في قاعدة البيانات"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"الملف غير موجود: {file_path}")
        
        # إضافة الوثيقة
        cursor = self.conn.execute('''
        INSERT OR REPLACE INTO documents (name, title, file_path, pages_count)
        VALUES (?, ?, ?, ?)
        ''', (document_name, title, file_path, 0))
        
        document_id = cursor.lastrowid
        
        # حذف المواد القديمة إذا كانت موجودة
        self.conn.execute('DELETE FROM articles WHERE document_id = ?', (document_id,))
        
        # تحليل وفهرسة المحتوى
        articles = self.parse_markdown_document(file_path, document_name)
        
        # إدراج المواد في قاعدة البيانات
        for article in articles:
            self.conn.execute('''
            INSERT INTO articles 
            (document_id, page_number, chapter, section, article_number, title, content, article_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                document_id, article.page_number, article.chapter, article.section,
                article.article_number, article.title, article.content, article.article_type
            ))
        
        # تحديث عدد الصفحات
        max_page = max([a.page_number for a in articles]) if articles else 0
        self.conn.execute('UPDATE documents SET pages_count = ? WHERE id = ?', (max_page, document_id))
        
        self.conn.commit()
        print(f"✅ تم فهرسة الوثيقة '{document_name}' بنجاح!")
        return len(articles)

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """البحث في المحتوى المفهرس"""
        # تنظيف الاستعلام
        clean_query = query.strip()
        if not clean_query:
            return []
        
        # البحث باستخدام FTS5
        cursor = self.conn.execute('''
        SELECT 
            a.id,
            a.document_id,
            d.name as document_name,
            d.title as document_title,
            a.page_number,
            a.chapter,
            a.section,
            a.article_number,
            a.title,
            a.content,
            a.article_type,
            articles_fts.rank
        FROM articles_fts 
        JOIN articles a ON articles_fts.rowid = a.id
        JOIN documents d ON a.document_id = d.id
        WHERE articles_fts MATCH ?
        ORDER BY articles_fts.rank
        LIMIT ?
        ''', (clean_query, limit))
        
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            # تمييز النص المطابق
            result['highlighted_content'] = self._highlight_matches(result['content'], clean_query)
            results.append(result)
        
        return results

    def _highlight_matches(self, text: str, query: str) -> str:
        """تمييز الكلمات المطابقة في النص"""
        words = query.split()
        highlighted_text = text
        
        for word in words:
            if len(word) > 2:  # تجنب الكلمات القصيرة جداً
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                highlighted_text = pattern.sub(f'**{word}**', highlighted_text)
        
        return highlighted_text

    def get_article_by_number(self, article_number: str, document_name: str = None) -> Optional[Dict]:
        """الحصول على مادة قانونية برقمها"""
        query = '''
        SELECT 
            a.id, d.name as document_name, d.title as document_title,
            a.page_number, a.chapter, a.section, a.article_number,
            a.title, a.content, a.article_type
        FROM articles a
        JOIN documents d ON a.document_id = d.id
        WHERE a.article_number = ?
        '''
        params = [article_number]
        
        if document_name:
            query += ' AND d.name = ?'
            params.append(document_name)
        
        cursor = self.conn.execute(query, params)
        row = cursor.fetchone()
        
        return dict(row) if row else None

    def get_statistics(self) -> Dict:
        """إحصائيات قاعدة البيانات"""
        stats = {}
        
        # عدد الوثائق
        cursor = self.conn.execute('SELECT COUNT(*) FROM documents')
        stats['documents_count'] = cursor.fetchone()[0]
        
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

    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if self.conn:
            self.conn.close()

def main():
    """اختبار النظام"""
    print("🔍 نظام فهرسة القوانين البحرينية")
    print("=" * 50)
    
    # إنشاء محرك البحث
    engine = LegalSearchEngine()
    
    # فهرسة وثيقة قانون العمل
    document_path = "docs_exports/document.md"
    if os.path.exists(document_path):
        engine.index_document(
            document_path, 
            "قانون العمل في القطاع الأهلي", 
            "قانون رقم (36) لسنة 2012"
        )
        
        # عرض الإحصائيات
        stats = engine.get_statistics()
        print(f"\n📊 الإحصائيات:")
        print(f"   📄 عدد الوثائق: {stats['documents_count']}")
        print(f"   📝 عدد المواد: {stats['articles_count']}")
        print(f"   📋 تفصيل المواد: {stats['articles_by_type']}")
        
        # اختبار البحث
        test_queries = [
            "العامل",
            "الأجر",
            "صاحب العمل",
            "عقد العمل"
        ]
        
        print(f"\n🔍 اختبار البحث:")
        for query in test_queries:
            results = engine.search(query, limit=3)
            print(f"\n🔎 البحث عن: '{query}' - {len(results)} نتيجة")
            for result in results[:2]:  # عرض أول نتيجتين
                print(f"   📄 المادة ({result['article_number']}) - الصفحة {result['page_number']}")
                print(f"   📝 {result['content'][:100]}...")
    else:
        print("❌ لم يتم العثور على ملف الوثيقة!")
    
    engine.close()

if __name__ == "__main__":
    main()
