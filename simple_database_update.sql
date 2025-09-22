-- تحديث مبسط لقاعدة البيانات - عمودين فقط
-- شغل هذا في Supabase SQL Editor

-- إضافة عمودين أساسيين فقط لجدول documents
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS extracted_title TEXT,
ADD COLUMN IF NOT EXISTS document_type TEXT DEFAULT 'غير محدد';

-- إضافة فهرس للبحث السريع
CREATE INDEX IF NOT EXISTS idx_documents_extracted_title ON documents(extracted_title);
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents(document_type);

-- إنشاء view بسيط للاستعلامات
CREATE OR REPLACE VIEW documents_simple AS
SELECT 
    id,
    filename,
    extracted_title,
    document_type,
    status,
    upload_date,
    file_size
FROM documents
ORDER BY upload_date DESC;

-- function بسيط للبحث
CREATE OR REPLACE FUNCTION search_documents_simple(search_term TEXT DEFAULT NULL)
RETURNS TABLE (
    document_id UUID,
    filename TEXT,
    extracted_title TEXT,
    document_type TEXT,
    match_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.filename,
        d.extracted_title,
        d.document_type,
        CASE 
            WHEN d.extracted_title ILIKE '%' || search_term || '%' THEN 'عنوان'
            WHEN d.filename ILIKE '%' || search_term || '%' THEN 'اسم الملف'
            ELSE 'مطابق'
        END as match_type
    FROM documents d
    WHERE 
        search_term IS NULL OR 
        d.extracted_title ILIKE '%' || search_term || '%' OR 
        d.filename ILIKE '%' || search_term || '%'
    ORDER BY d.upload_date DESC;
END;
$$ LANGUAGE plpgsql;

-- إضافة تعليقات
COMMENT ON COLUMN documents.extracted_title IS 'العنوان المستخرج من المحتوى';
COMMENT ON COLUMN documents.document_type IS 'نوع الوثيقة (قانون، مرسوم، نظام، إلخ)';

-- انتهى التحديث المبسط
