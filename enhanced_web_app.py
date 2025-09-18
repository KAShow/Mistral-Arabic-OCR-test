#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تطبيق ويب محسن لنظام البحث في القوانين البحرينية
مع دعم عرض الصفحات الكاملة
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import os
import uvicorn
from urllib.parse import unquote, quote
from legal_search import LegalSearchEngine
from enhanced_legal_search import EnhancedLegalSearchEngine

# إنشاء تطبيق FastAPI
app = FastAPI(
    title="نظام البحث المحسن في القوانين البحرينية",
    description="نظام بحث متقدم للوثائق القانونية مع عرض الصفحات الكاملة",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# إعداد الملفات الثابتة والقوالب
if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("templates"):
    os.makedirs("templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# إضافة دوال مساعدة للقوالب
def url_encode(text):
    """ترميز النص للـ URL"""
    return quote(str(text), safe='')

def url_decode(text):
    """فك ترميز النص من الـ URL"""
    return unquote(str(text))

# تسجيل الدوال في Jinja2
templates.env.filters['urlencode'] = url_encode
templates.env.filters['urldecode'] = url_decode

# إنشاء محركي البحث
search_engine = None
enhanced_engine = None

def get_search_engine():
    """الحصول على محرك البحث العادي"""
    global search_engine
    if search_engine is None:
        search_engine = LegalSearchEngine()
    return search_engine

def get_enhanced_search_engine():
    """الحصول على محرك البحث المحسن"""
    global enhanced_engine
    if enhanced_engine is None:
        enhanced_engine = EnhancedLegalSearchEngine()
    return enhanced_engine

# نماذج البيانات
class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 10

class SearchResult(BaseModel):
    id: int
    document_name: str
    document_title: Optional[str]
    page_number: int
    chapter: Optional[str]
    section: Optional[str]
    article_number: Optional[str]
    title: Optional[str]
    content: str
    article_type: str
    highlighted_content: Optional[str]

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    execution_time: float

class Statistics(BaseModel):
    documents_count: int
    articles_count: int
    pages_count: Optional[int]
    articles_by_type: dict

# المسارات الرئيسية

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """الصفحة الرئيسية"""
    engine = get_search_engine()
    stats = engine.get_statistics()
    
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats
    })
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.get("/api/stats", response_model=Statistics)
async def get_statistics():
    """الحصول على إحصائيات قاعدة البيانات"""
    engine = get_enhanced_search_engine()
    stats = engine.get_statistics()
    
    return Statistics(
        documents_count=stats['documents_count'],
        articles_count=stats['articles_count'],
        pages_count=stats.get('pages_count', 0),
        articles_by_type=stats.get('articles_by_type', {})
    )

@app.post("/api/search", response_model=SearchResponse)
async def search_documents(search_query: SearchQuery):
    """البحث في الوثائق"""
    import time
    start_time = time.time()
    
    engine = get_enhanced_search_engine()
    
    if not search_query.query.strip():
        raise HTTPException(status_code=400, detail="يرجى إدخال كلمة أو عبارة للبحث")
    
    # تنفيذ البحث
    results = engine.search_enhanced(search_query.query, limit=search_query.limit)
    
    # تحويل النتائج إلى نموذج البيانات
    search_results = []
    for result in results:
        search_results.append(SearchResult(
            id=result['id'],
            document_name=result['document_name'],
            document_title=result.get('document_title'),
            page_number=result['page_number'],
            chapter=result.get('chapter'),
            section=result.get('section'),
            article_number=result.get('article_number'),
            title=result.get('title'),
            content=result['content'],
            article_type=result['article_type'],
            highlighted_content=result.get('highlighted_content', result['content'])
        ))
    
    execution_time = time.time() - start_time
    
    return SearchResponse(
        query=search_query.query,
        results=search_results,
        total_results=len(search_results),
        execution_time=round(execution_time, 3)
    )

@app.get("/api/search", response_model=SearchResponse)
async def search_documents_get(query: str, limit: Optional[int] = 10):
    """البحث عبر GET (للاختبار)"""
    search_query = SearchQuery(query=query, limit=limit)
    return await search_documents(search_query)

@app.post("/search", response_class=HTMLResponse)
async def search_form(request: Request, query: str = Form(...)):
    """معالجة نموذج البحث"""
    engine = get_enhanced_search_engine()
    
    if not query.strip():
        response = templates.TemplateResponse("index.html", {
            "request": request,
            "error": "يرجى إدخال كلمة أو عبارة للبحث",
            "stats": engine.get_statistics()
        })
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        return response
    
    # تنفيذ البحث
    results = engine.search_enhanced(query, limit=20)
    
    response = templates.TemplateResponse("results.html", {
        "request": request,
        "query": query,
        "results": results,
        "total_results": len(results)
    })
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

# المسارات الجديدة لعرض الصفحات الكاملة

@app.get("/page/{document_name}/{page_number}", response_class=HTMLResponse)
async def view_full_page(request: Request, document_name: str, page_number: int, highlight: str = ""):
    """عرض الصفحة الكاملة مع تمييز النص"""
    engine = get_enhanced_search_engine()
    
    # فك تشفير اسم الوثيقة والنص المميز
    decoded_document_name = unquote(document_name)
    decoded_highlight = unquote(highlight) if highlight else ""
    
    # الحصول على محتوى الصفحة
    page_data = engine.get_page_with_highlighted_text(decoded_document_name, page_number, decoded_highlight)
    
    if not page_data:
        raise HTTPException(status_code=404, detail="الصفحة غير موجودة")
    
    # الحصول على معلومات الوثيقة
    stats = engine.get_statistics()
    
    response = templates.TemplateResponse("page_viewer.html", {
        "request": request,
        "page_data": page_data,
        "document_name": decoded_document_name,
        "page_number": page_number,
        "highlight": decoded_highlight,
        "total_pages": stats.get('pages_count', 1)
    })
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response

@app.get("/api/page/{document_name}/{page_number}")
async def get_page_api(document_name: str, page_number: int, highlight: str = ""):
    """API للحصول على محتوى الصفحة"""
    engine = get_enhanced_search_engine()
    
    # فك تشفير اسم الوثيقة والنص المميز
    decoded_document_name = unquote(document_name)
    decoded_highlight = unquote(highlight) if highlight else ""
    
    page_data = engine.get_page_with_highlighted_text(decoded_document_name, page_number, decoded_highlight)
    
    if not page_data:
        raise HTTPException(status_code=404, detail="الصفحة غير موجودة")
    
    return page_data

@app.get("/article/{article_id}")
async def get_article(article_id: int):
    """الحصول على مادة قانونية بالمعرف"""
    engine = get_enhanced_search_engine()
    
    # البحث عن المادة بالمعرف
    cursor = engine.conn.execute('''
    SELECT 
        a.id, d.name as document_name, d.title as document_title,
        a.page_number, a.chapter, a.section, a.article_number,
        a.title, a.content, a.article_type
    FROM articles a
    JOIN documents d ON a.document_id = d.id
    WHERE a.id = ?
    ''', (article_id,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="المادة غير موجودة")
    
    return dict(row)

# معالجة الأخطاء
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {
        "request": request
    }, status_code=404)

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return templates.TemplateResponse("500.html", {
        "request": request
    }, status_code=500)

# إعداد التطبيق عند البدء
@app.on_event("startup")
async def startup_event():
    """إعداد التطبيق عند البدء"""
    print(" بدء تشغيل خادم البحث القانوني المحسن...")
    
    # التأكد من وجود قاعدة البيانات المحسنة
    if not os.path.exists("enhanced_legal_database.db"):
        print(" لم يتم العثور على قاعدة البيانات المحسنة، سيتم إنشاؤها...")
        engine = get_enhanced_search_engine()
        
        # فهرسة الوثيقة إذا كانت موجودة
        if os.path.exists("docs_exports/document.md"):
            engine.index_document_enhanced(
                "docs_exports/document.md",
                "قانون العمل في القطاع الأهلي",
                "قانون رقم (36) لسنة 2012"
            )
            print(" تم فهرسة قانون العمل بنجاح في قاعدة البيانات المحسنة")
    else:
        # تحميل محرك البحث المحسن
        engine = get_enhanced_search_engine()
        stats = engine.get_statistics()
        print(f" تم تحميل قاعدة البيانات المحسنة: {stats['documents_count']} وثيقة، {stats.get('pages_count', 0)} صفحة، {stats['articles_count']} مادة")

@app.on_event("shutdown")
async def shutdown_event():
    """تنظيف الموارد عند الإغلاق"""
    global search_engine, enhanced_engine
    if search_engine:
        search_engine.close()
    if enhanced_engine:
        enhanced_engine.close()
        print(" تم إغلاق محركات البحث")

if __name__ == "__main__":
    print(" نظام البحث المحسن في القوانين البحرينية")
    print("=" * 50)
    print(" سيتم تشغيل الخادم على: http://localhost:8000")
    print(" واجهة برمجة التطبيقات: http://localhost:8000/api/docs")
    print(" عرض الصفحات الكاملة: http://localhost:8000/page/[document]/[page]")
    print("=" * 50)
    
    uvicorn.run(
        "enhanced_web_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
