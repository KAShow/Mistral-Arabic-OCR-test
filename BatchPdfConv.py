import os
import sys
import base64
import csv
import time
import logging
import re
from mistralai import Mistral
from dotenv import load_dotenv
load_dotenv() 


# Configuration
DOC_DIR = "docs_import"
EXPORT_DIR = "docs_exports"
DB_CSV = "processed_files.csv"
LOG_FILE = "conversion.log"
MAX_RETRIES = 5
INITIAL_BACKOFF = 1  # in seconds

# Initialize logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
)

# Ensure API key is set via environment variable
API_KEY = "97ZQlsV45YrDusgZRwjArWGbh3nerFPb"
if not API_KEY:
    print("Error: MISTRAL_API_KEY environment variable not set.")
    sys.exit(1)

client = Mistral(api_key=API_KEY)

FIELDNAMES = ['filename', 'status', 'attempts', 'error']


def clean_repetitive_text(text, max_consecutive_repeats=3):
    """
    تنظيف النص من التكرار المتتالي الزائد
    
    Args:
        text: النص المراد تنظيفه
        max_consecutive_repeats: الحد الأقصى للتكرار المتتالي المسموح به
    
    Returns:
        النص المنظف من التكرار
    """
    if not text or len(text) < 20:
        return text
    
    # تقسيم النص إلى كلمات
    words = text.split()
    
    if len(words) < 10:
        return text
    
    # تنظيف التكرار المتتالي
    cleaned_words = []
    consecutive_count = 1
    
    for i, word in enumerate(words):
        if i > 0 and word == words[i-1]:
            consecutive_count += 1
            # السماح بتكرار محدود فقط
            if consecutive_count <= max_consecutive_repeats:
                cleaned_words.append(word)
        else:
            consecutive_count = 1
            cleaned_words.append(word)
    
    # إذا كان النص المنظف أقل من 20% من الأصلي، هناك مشكلة كبيرة
    if len(cleaned_words) < len(words) * 0.2:
        # احتفظ بأول جزء معقول فقط
        return ' '.join(words[:100]) + '\n\n**[تحذير: تم اكتشاف تكرار زائد في هذا الجزء من النص - قد تكون هناك مشكلة في قراءة OCR]**'
    
    result = ' '.join(cleaned_words)
    
    # تنظيف الأسطر الطويلة جداً
    lines = result.split('\n')
    cleaned_lines = []
    for line in lines:
        if len(line) > 2000:  # سطر طويل جداً = مشكلة
            cleaned_lines.append(line[:500] + '\n\n**[تحذير: النص مقطوع بسبب تكرار زائد]**')
        else:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def ensure_export_directory():
    """Ensure the export directory exists."""
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
        print(f"Created export directory: {EXPORT_DIR}")


def load_processed():
    """Load processed file records from CSV into a dict."""
    processed = {}
    if os.path.exists(DB_CSV):
        with open(DB_CSV, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                processed[row['filename']] = row
    return processed


def append_to_db(record):
    """Append a processing record to the CSV database."""
    file_exists = os.path.exists(DB_CSV)
    with open(DB_CSV, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)


def get_pdf_files():
    """List all PDF files in the DOC_DIR folder and its subdirectories."""
    if not os.path.isdir(DOC_DIR):
        print(f"Error: Directory '{DOC_DIR}' not found.")
        sys.exit(1)
    
    pdf_files = []
    for root, dirs, files in os.walk(DOC_DIR):
        for file in files:
            if file.lower().endswith('.pdf'):
                # Get relative path from DOC_DIR
                rel_path = os.path.relpath(os.path.join(root, file), DOC_DIR)
                pdf_files.append(rel_path)
    
    return pdf_files


def encode_pdf(pdf_path):
    """Encode the PDF file to a base64 string."""
    try:
        with open(pdf_path, "rb") as pdf_file:
            return base64.b64encode(pdf_file.read()).decode('utf-8')
    except Exception as e:
        logging.error(f"Failed to encode {pdf_path}: {e}")
        return None


def convert_pdf_to_markdown(pdf_filename):
    """Perform OCR on the PDF and write the output as a markdown file in the export directory."""
    full_path = os.path.join(DOC_DIR, pdf_filename)
    b64 = encode_pdf(full_path)
    if not b64:
        raise RuntimeError("PDF encoding failed.")

    # Call Mistral OCR
    response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{b64}"
        },
        include_image_base64=False
    )

    # Create output directory structure
    output_name = pdf_filename.rsplit('.', 1)[0] + '.md'
    output_path = os.path.join(EXPORT_DIR, output_name)
    
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w', encoding='utf-8') as md_file:
        for page in response.pages:
            md_file.write(f"## Page {page.index + 1}\n\n")
            # تنظيف النص من التكرار قبل الكتابة
            cleaned_markdown = clean_repetitive_text(page.markdown)
            md_file.write(cleaned_markdown + "\n\n")
    
    print(f"Saved markdown file: {output_path}")


def main():
    # Ensure export directory exists
    ensure_export_directory()
    
    processed = load_processed()
    all_files = get_pdf_files()
    total = len(all_files)
    succeeded = sum(1 for r in processed.values() if r['status'] == 'success')
    to_do = [f for f in all_files if processed.get(f, {}).get('status') != 'success']

    print(f"Found {total} PDF files in '{DOC_DIR}/'. {succeeded} already converted. {len(to_do)} remaining.")
    print(f"Output will be saved to '{EXPORT_DIR}/' directory.")

    converted_count = 0
    for idx, pdf in enumerate(to_do, start=1):
        print(f"[{idx}/{len(to_do)}] Processing: {pdf}")
        attempts = 0
        backoff = INITIAL_BACKOFF
        success = False

        while attempts < MAX_RETRIES and not success:
            attempts += 1
            try:
                convert_pdf_to_markdown(pdf)
                success = True
                converted_count += 1
                append_to_db({'filename': pdf, 'status': 'success', 'attempts': attempts, 'error': ''})
                print(f"Success: {pdf} (attempt {attempts})")
                print(f"Waiting for the next file...")
                time.sleep(3)
            except Exception as e:
                error_msg = str(e)
                append_to_db({'filename': pdf, 'status': 'error', 'attempts': attempts, 'error': error_msg})
                logging.error(f"{pdf} attempt {attempts} failed: {error_msg}")
                print(f"Error converting {pdf} on attempt {attempts}: {error_msg}")
                if attempts < MAX_RETRIES:
                    print(f"Retrying in {backoff} seconds...")
                    time.sleep(backoff)
                    backoff *= 2

        if not success:
            print(f"Failed: {pdf} after {attempts} attempts.")

    print(f"\nConversion complete. Total successful conversions: {converted_count} out of {len(to_do)}.")
    print(f"All converted files are saved in '{EXPORT_DIR}/' directory.")


if __name__ == '__main__':
    main()
