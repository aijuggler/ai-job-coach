import docx2txt
import tempfile, os

def docx_bytes_to_text(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        text = docx2txt.process(tmp_path) or ""
    finally:
        os.remove(tmp_path)
    return text
