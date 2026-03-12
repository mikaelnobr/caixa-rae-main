import pdfplumber


def get_text_with_layout(pdf_path: str) -> str:
    """Extrai texto do PDF preservando o layout visual."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            ext = page.extract_text(layout=True)
            if ext:
                text += ext + "\n"
    return text
