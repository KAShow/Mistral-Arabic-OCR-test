#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تطبيق ويب لنظام البحث في القوانين البحرينية
باستخدام FastAPI
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import os
import uvicorn
from legal_search import LegalSearchEngine

# إنشاء تطبيق FastAPI
app = FastAPI(
    title="نظام البحث في القوانين البحرينية",
    description="نظام بحث متقدم للوثائق القانونية باللغة العربية",
    version="1.0.0",
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

# إنشاء محرك البحث العام
search_engine = None

def get_search_engine():
    """الحصول على محرك البحث أو إنشاؤه"""
    global search_engine
    if search_engine is None:
        search_engine = LegalSearchEngine()
    return search_engine

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
    articles_by_type: dict

# المسارات الرئيسية

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """الصفحة الرئيسية"""
    engine = get_search_engine()
    stats = engine.get_statistics()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats
    })

@app.get("/api/stats", response_model=Statistics)
async def get_statistics():
    """الحصول على إحصائيات قاعدة البيانات"""
    engine = get_search_engine()
    stats = engine.get_statistics()
    
    return Statistics(
        documents_count=stats['documents_count'],
        articles_count=stats['articles_count'],
        articles_by_type=stats.get('articles_by_type', {})
    )

@app.post("/api/search", response_model=SearchResponse)
async def search_documents(search_query: SearchQuery):
    """البحث في الوثائق"""
    import time
    start_time = time.time()
    
    engine = get_search_engine()
    
    if not search_query.query.strip():
        raise HTTPException(status_code=400, detail="يرجى إدخال كلمة أو عبارة للبحث")
    
    # تنفيذ البحث
    results = engine.search(search_query.query, limit=search_query.limit)
    
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
    engine = get_search_engine()
    
    if not query.strip():
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "يرجى إدخال كلمة أو عبارة للبحث",
            "stats": engine.get_statistics()
        })
    
    # تنفيذ البحث
    results = engine.search(query, limit=20)
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "query": query,
        "results": results,
        "total_results": len(results)
    })

@app.get("/article/{article_id}")
async def get_article(article_id: int):
    """الحصول على مادة قانونية بالمعرف"""
    engine = get_search_engine()
    
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
    print("🚀 بدء تشغيل خادم البحث القانوني...")
    
    # التأكد من وجود قاعدة البيانات
    if not os.path.exists("legal_database.db"):
        print("⚠️ لم يتم العثور على قاعدة البيانات، سيتم إنشاؤها...")
        engine = get_search_engine()
        
        # فهرسة الوثيقة إذا كانت موجودة
        if os.path.exists("docs_exports/document.md"):
            engine.index_document(
                "docs_exports/document.md",
                "قانون العمل في القطاع الأهلي",
                "قانون رقم (36) لسنة 2012"
            )
            print("✅ تم فهرسة قانون العمل بنجاح")
    else:
        # تحميل محرك البحث
        engine = get_search_engine()
        stats = engine.get_statistics()
        print(f"✅ تم تحميل قاعدة البيانات: {stats['documents_count']} وثيقة، {stats['articles_count']} مادة")

@app.on_event("shutdown")
async def shutdown_event():
    """تنظيف الموارد عند الإغلاق"""
    global search_engine
    if search_engine:
        search_engine.close()
        print("👋 تم إغلاق محرك البحث")

if __name__ == "__main__":
    print("🔍 نظام البحث في القوانين البحرينية")
    print("=" * 50)
    print("🌐 سيتم تشغيل الخادم على: http://localhost:8000")
    print("📚 واجهة برمجة التطبيقات: http://localhost:8000/api/docs")
    print("=" * 50)
    
    uvicorn.run(
        "web_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
