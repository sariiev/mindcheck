import io

from pypdf import PdfReader

async def parse_file(content: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    elif content_type in ["text/plain", "text/markdown"]:
        return content.decode("utf-8")
    else:
        raise ValueError(f"Unsupported file type: {content_type}")