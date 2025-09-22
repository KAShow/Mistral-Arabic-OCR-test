-- تحديث هيكل قاعدة البيانات للتحسينات الجديدة
-- يجب تشغيل هذا في Supabase SQL Editor

-- 1. تحديث جدول الوثائق بالحقول الجديدة
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS extracted_title TEXT,
ADD COLUMN IF NOT EXISTS document_type TEXT DEFAULT 'غير محدد',
ADD COLUMN IF NOT EXISTS content_quality_score DECIMAL(3,2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS processing_notes JSONB DEFAULT '{}';

-- 2. تحديث جدول محتوى الوثائق
ALTER TABLE document_content 
ADD COLUMN IF NOT EXISTS cleaned_content TEXT,
ADD COLUMN IF NOT EXISTS has_images BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS content_type TEXT DEFAULT 'نص';

-- 3. تحديث جدول الفهرسة
ALTER TABLE document_index 
ADD COLUMN IF NOT EXISTS chunk_type TEXT DEFAULT 'paragraph_group',
ADD COLUMN IF NOT EXISTS confidence DECIMAL(3,2) DEFAULT 0.0;

-- 4. إنشاء جدول جديد لهيكل الوثائق القانونية
CREATE TABLE IF NOT EXISTS document_structure (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    structure_type TEXT NOT NULL, -- 'باب', 'فصل', 'مادة', 'فقرة', 'بند'
    structure_number TEXT,
    structure_title TEXT,
    content_preview TEXT,
    page_number INTEGER,
    position_in_document INTEGER,
    parent_structure_id UUID REFERENCES document_structure(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. إنشاء جدول للأرقام والتواريخ القانونية
CREATE TABLE IF NOT EXISTS document_legal_numbers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    number_type TEXT NOT NULL, -- 'سنة', 'رقم_قانون', 'تاريخ', 'مبلغ', 'نسبة'
    number_value TEXT NOT NULL,
    full_context TEXT,
    page_number INTEGER,
    position_in_document INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. إنشاء جدول لإحصائيات المعالجة
CREATE TABLE IF NOT EXISTS processing_statistics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    total_pages INTEGER DEFAULT 0,
    useful_pages INTEGER DEFAULT 0,
    total_original_length INTEGER DEFAULT 0,
    total_cleaned_length INTEGER DEFAULT 0,
    compression_ratio DECIMAL(4,3) DEFAULT 0.0,
    title_confidence DECIMAL(3,2) DEFAULT 0.0,
    indexing_confidence DECIMAL(3,2) DEFAULT 0.0,
    improvements_applied JSONB DEFAULT '{}',
    processing_time_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. إنشاء فهارس للبحث السريع
CREATE INDEX IF NOT EXISTS idx_documents_extracted_title ON documents(extracted_title);
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_quality_score ON documents(content_quality_score);

CREATE INDEX IF NOT EXISTS idx_document_content_content_type ON document_content(content_type);
CREATE INDEX IF NOT EXISTS idx_document_content_has_images ON document_content(has_images);

CREATE INDEX IF NOT EXISTS idx_document_structure_type ON document_structure(structure_type);
CREATE INDEX IF NOT EXISTS idx_document_structure_number ON document_structure(structure_number);
CREATE INDEX IF NOT EXISTS idx_document_structure_parent ON document_structure(parent_structure_id);

CREATE INDEX IF NOT EXISTS idx_document_legal_numbers_type ON document_legal_numbers(number_type);
CREATE INDEX IF NOT EXISTS idx_document_legal_numbers_value ON document_legal_numbers(number_value);

CREATE INDEX IF NOT EXISTS idx_processing_stats_quality ON processing_statistics(title_confidence, indexing_confidence);

-- 8. إنشاء views مفيدة للاستعلامات
CREATE OR REPLACE VIEW documents_enhanced AS
SELECT 
    d.id,
    d.filename,
    d.extracted_title,
    d.document_type,
    d.content_quality_score,
    d.status,
    d.upload_date,
    ps.total_pages,
    ps.useful_pages,
    ps.title_confidence,
    ps.indexing_confidence,
    (ps.useful_pages::float / NULLIF(ps.total_pages, 0)) as useful_pages_ratio
FROM documents d
LEFT JOIN processing_statistics ps ON d.id = ps.document_id;

CREATE OR REPLACE VIEW document_content_summary AS
SELECT 
    dc.document_id,
    d.extracted_title,
    COUNT(*) as total_pages,
    COUNT(CASE WHEN dc.content_type = 'نص' THEN 1 END) as text_pages,
    COUNT(CASE WHEN dc.has_images THEN 1 END) as pages_with_images,
    SUM(LENGTH(dc.cleaned_content)) as total_content_length,
    AVG(LENGTH(dc.cleaned_content)) as avg_page_length
FROM document_content dc
JOIN documents d ON dc.document_id = d.id
GROUP BY dc.document_id, d.extracted_title;

CREATE OR REPLACE VIEW legal_structure_summary AS
SELECT 
    ds.document_id,
    d.extracted_title,
    COUNT(CASE WHEN ds.structure_type = 'باب' THEN 1 END) as sections_count,
    COUNT(CASE WHEN ds.structure_type = 'فصل' THEN 1 END) as chapters_count,
    COUNT(CASE WHEN ds.structure_type = 'مادة' THEN 1 END) as articles_count,
    COUNT(CASE WHEN ds.structure_type = 'فقرة' THEN 1 END) as paragraphs_count
FROM document_structure ds
JOIN documents d ON ds.document_id = d.id
GROUP BY ds.document_id, d.extracted_title;

-- 9. إنشاء function للبحث المتقدم
CREATE OR REPLACE FUNCTION search_documents_advanced(
    search_term TEXT DEFAULT NULL,
    doc_type TEXT DEFAULT NULL,
    min_quality DECIMAL DEFAULT 0.0,
    has_structure BOOLEAN DEFAULT NULL
)
RETURNS TABLE (
    document_id UUID,
    filename TEXT,
    extracted_title TEXT,
    document_type TEXT,
    quality_score DECIMAL,
    match_reason TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.filename,
        d.extracted_title,
        d.document_type,
        d.content_quality_score,
        CASE 
            WHEN search_term IS NOT NULL AND d.extracted_title ILIKE '%' || search_term || '%' THEN 'عنوان'
            WHEN search_term IS NOT NULL AND d.filename ILIKE '%' || search_term || '%' THEN 'اسم الملف'
            ELSE 'مطابق للمعايير'
        END as match_reason
    FROM documents d
    LEFT JOIN legal_structure_summary lss ON d.id = lss.document_id
    WHERE 
        (search_term IS NULL OR 
         d.extracted_title ILIKE '%' || search_term || '%' OR 
         d.filename ILIKE '%' || search_term || '%')
        AND (doc_type IS NULL OR d.document_type = doc_type)
        AND d.content_quality_score >= min_quality
        AND (has_structure IS NULL OR 
             (has_structure = TRUE AND lss.articles_count > 0) OR
             (has_structure = FALSE AND (lss.articles_count IS NULL OR lss.articles_count = 0)))
    ORDER BY d.content_quality_score DESC, d.upload_date DESC;
END;
$$ LANGUAGE plpgsql;

-- 10. إضافة تعليقات على الجداول والأعمدة
COMMENT ON COLUMN documents.extracted_title IS 'العنوان المستخرج من المحتوى';
COMMENT ON COLUMN documents.document_type IS 'نوع الوثيقة (قانون، مرسوم، نظام، إلخ)';
COMMENT ON COLUMN documents.content_quality_score IS 'درجة جودة المحتوى (0-1)';
COMMENT ON COLUMN documents.processing_notes IS 'ملاحظات المعالجة والتحسينات المطبقة';

COMMENT ON COLUMN document_content.cleaned_content IS 'المحتوى بعد التنظيف';
COMMENT ON COLUMN document_content.has_images IS 'يحتوي على مراجع صور';
COMMENT ON COLUMN document_content.content_type IS 'نوع المحتوى (نص، صورة، غير مفيد)';

COMMENT ON TABLE document_structure IS 'هيكل الوثائق القانونية (أبواب، فصول، مواد)';
COMMENT ON TABLE document_legal_numbers IS 'الأرقام والتواريخ القانونية المستخرجة';
COMMENT ON TABLE processing_statistics IS 'إحصائيات عملية المعالجة والتحسين';

-- 11. إنشاء triggers للتحديث التلقائي
CREATE OR REPLACE FUNCTION update_document_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- تحديث إحصائيات الوثيقة عند إضافة محتوى جديد
    INSERT INTO processing_statistics (document_id, total_pages, useful_pages)
    SELECT 
        NEW.document_id,
        COUNT(*),
        COUNT(CASE WHEN content_type = 'نص' THEN 1 END)
    FROM document_content 
    WHERE document_id = NEW.document_id
    ON CONFLICT (document_id) DO UPDATE SET
        total_pages = EXCLUDED.total_pages,
        useful_pages = EXCLUDED.useful_pages;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- تطبيق trigger على جدول المحتوى
DROP TRIGGER IF EXISTS trigger_update_document_stats ON document_content;
CREATE TRIGGER trigger_update_document_stats
    AFTER INSERT OR UPDATE ON document_content
    FOR EACH ROW
    EXECUTE FUNCTION update_document_stats();

-- إنهاء السكربت
-- تم إنشاء الهيكل المحسن لقاعدة البيانات
