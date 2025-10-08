import os
import sys
from pypdf import PdfReader, PdfWriter

def split_pdf(input_pdf_path, output_folder=None):
    """
    تقسيم ملف PDF إلى ملفات منفصلة لكل صفحة
    
    Args:
        input_pdf_path: مسار ملف PDF المراد تقسيمه
        output_folder: مجلد الإخراج (اختياري، افتراضياً نفس مجلد الملف الأصلي)
    """
    # التحقق من وجود الملف
    if not os.path.exists(input_pdf_path):
        print(f"خطأ: الملف '{input_pdf_path}' غير موجود")
        return
    
    # إنشاء مجلد الإخراج
    if output_folder is None:
        base_name = os.path.splitext(os.path.basename(input_pdf_path))[0]
        output_folder = f"{base_name}_pages"
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"تم إنشاء المجلد: {output_folder}")
    
    # قراءة ملف PDF
    try:
        reader = PdfReader(input_pdf_path)
        total_pages = len(reader.pages)
        print(f"عدد الصفحات: {total_pages}")
        
        # تقسيم كل صفحة إلى ملف منفصل
        for page_num in range(total_pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])
            
            # تسمية الملف بترقيم مرتب
            output_filename = f"page_{page_num + 1:03d}.pdf"
            output_path = os.path.join(output_folder, output_filename)
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            print(f"تم حفظ: {output_filename}")
        
        print(f"\nتم التقسيم بنجاح! الملفات محفوظة في: {output_folder}")
        
    except Exception as e:
        print(f"خطأ أثناء المعالجة: {e}")


def main():
    if len(sys.argv) < 2:
        print("الاستخدام: python split_pdf.py <مسار_ملف_PDF> [مجلد_الإخراج]")
        print("\nمثال:")
        print("  python split_pdf.py document.pdf")
        print("  python split_pdf.py document.pdf output_folder")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_folder = sys.argv[2] if len(sys.argv) > 2 else None
    
    split_pdf(input_pdf, output_folder)


if __name__ == '__main__':
    main()


