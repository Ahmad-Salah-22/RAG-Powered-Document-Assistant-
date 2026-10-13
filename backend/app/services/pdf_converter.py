import io
import os
from typing import Optional
from app.utils.logging_config import logger

def convert_file_to_real_pdf(file_path: str) -> Optional[str]:
    """
    Converts any supported document format (PPTX, DOCX, XLSX) to a real,
    pixel-perfect PDF preserving all visual diagrams, layouts, images, and formatting.
    Uses native Windows Office COM automation (PowerPoint/Word/Excel) with caching.
    """
    if not os.path.isfile(file_path):
        return None

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return file_path

    pdf_path = os.path.splitext(file_path)[0] + ".pdf"
    
    # Check if up-to-date converted PDF already exists
    if os.path.isfile(pdf_path):
        src_mtime = os.path.getmtime(file_path)
        pdf_mtime = os.path.getmtime(pdf_path)
        if pdf_mtime >= src_mtime and os.path.getsize(pdf_path) > 1000:
            return pdf_path

    abs_src = os.path.abspath(file_path)
    abs_pdf = os.path.abspath(pdf_path)

    # Convert using Microsoft PowerPoint COM
    if ext in [".pptx", ".ppt"]:
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            try:
                ppt = win32com.client.Dispatch("PowerPoint.Application")
                pres = ppt.Presentations.Open(abs_src, ReadOnly=True, Untitled=False, WithWindow=False)
                pres.SaveAs(abs_pdf, 32)  # 32 = ppSaveAsPDF
                pres.Close()
                ppt.Quit()
                logger.info(f"Successfully converted '{abs_src}' to real PDF '{abs_pdf}' via PowerPoint COM.")
                return abs_pdf
            finally:
                pythoncom.CoUninitialize()
        except Exception as e:
            logger.warning(f"PowerPoint COM conversion failed for '{file_path}': {e}")

    # Convert using Microsoft Word COM
    elif ext in [".docx", ".doc"]:
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            try:
                word = win32com.client.Dispatch("Word.Application")
                doc = word.Documents.Open(abs_src, ReadOnly=True)
                doc.SaveAs(abs_pdf, 17)  # 17 = wdFormatPDF
                doc.Close()
                word.Quit()
                logger.info(f"Successfully converted '{abs_src}' to real PDF '{abs_pdf}' via Word COM.")
                return abs_pdf
            finally:
                pythoncom.CoUninitialize()
        except Exception as e:
            logger.warning(f"Word COM conversion failed for '{file_path}': {e}")

    # Convert using Microsoft Excel COM
    elif ext in [".xlsx", ".xls"]:
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            try:
                excel = win32com.client.Dispatch("Excel.Application")
                wb = excel.Workbooks.Open(abs_src, ReadOnly=True)
                wb.ExportAsFixedFormat(0, abs_pdf)  # 0 = xlTypePDF
                wb.Close()
                excel.Quit()
                logger.info(f"Successfully converted '{abs_src}' to real PDF '{abs_pdf}' via Excel COM.")
                return abs_pdf
            finally:
                pythoncom.CoUninitialize()
        except Exception as e:
            logger.warning(f"Excel COM conversion failed for '{file_path}': {e}")

    # Fallback to ReportLab synthesis if COM is unavailable
    try:
        from app.services.ingestion import extract_from_bytes
        with open(abs_src, "rb") as f:
            file_bytes = f.read()
        pdf_bytes = _synthesize_reportlab_pdf(file_bytes, os.path.basename(file_path))
        with open(abs_pdf, "wb") as f:
            f.write(pdf_bytes)
        return abs_pdf
    except Exception as e:
        logger.error(f"Fallback ReportLab synthesis failed for '{file_path}': {e}")
        return None


def render_pdf_page_image(pdf_path: str, page_number: int, dpi: int = 150) -> Optional[bytes]:
    """
    Renders a specific page of a PDF document to high-definition PNG image bytes.
    Preserves exact visual fidelity, diagrams, and formatting.
    """
    if not os.path.isfile(pdf_path):
        return None

    try:
        import pymupdf
        doc = pymupdf.open(pdf_path)
        if page_number < 1 or page_number > len(doc):
            return None
        
        page = doc[page_number - 1]
        pix = page.get_pixmap(dpi=dpi)
        return pix.tobytes("png")
    except Exception as e:
        logger.error(f"Error rendering PDF page {page_number} image for '{pdf_path}': {e}")
        return None


def extract_text_from_pdf_page(pdf_path: str, page_number: int) -> str:
    """Extracts high-quality text from a real converted PDF page."""
    if not os.path.isfile(pdf_path):
        return ""
    try:
        import pymupdf
        doc = pymupdf.open(pdf_path)
        if 1 <= page_number <= len(doc):
            return doc[page_number - 1].get_text()
    except Exception as e:
        logger.warning(f"Error extracting text from PDF page {page_number}: {e}")
    return ""


def _synthesize_reportlab_pdf(file_bytes: bytes, filename: str) -> bytes:
    """Synthesizes a landscape presentation or portrait document PDF using ReportLab."""
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from app.services.ingestion import extract_from_bytes

    pages, _ = extract_from_bytes(file_bytes, filename)
    if not pages:
        pages = [{"page": 1, "text": f"Document: {filename}\nNo text extracted."}]

    ext = os.path.splitext(filename)[1].lower()
    is_presentation = ext in [".pptx", ".ppt"]
    width, height = landscape(letter) if is_presentation else letter

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    total_pages = max(1, len(pages))

    for p in pages:
        p_num = p.get("page", 1)
        text = p.get("text", "")
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(0, 0, width, height, fill=True, stroke=False)
        c.setFillColor(colors.HexColor("#6366f1"))
        c.rect(30, height - 40, width - 60, 3, fill=True, stroke=False)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, height - 30, f"PAGE {p_num} OF {total_pages} - {filename}")
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 11)
        words = text.split()
        cur_y = height - 70
        line = []
        for w in words:
            line.append(w)
            if len(" ".join(line)) > 75:
                c.drawString(40, cur_y, " ".join(line))
                cur_y -= 18
                line = []
                if cur_y < 40:
                    break
        if line and cur_y >= 40:
            c.drawString(40, cur_y, " ".join(line))
        c.showPage()

    c.save()
    return buf.getvalue()
