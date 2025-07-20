import pdfplumber
from io import BytesIO

def pdf_bytes_to_text(data: bytes) -> str:
    text_parts = []
    with pdfplumber.open(BytesIO(data)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t.strip():
                text_parts.append(t)
    return "\n".join(text_parts)
