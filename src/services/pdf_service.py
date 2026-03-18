import pdfplumber


class PdfService:
    """
    Serviço para extração de dados e texto de arquivos PDF.
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def get_text_with_layout(self) -> str:
        """
        Extrai texto do PDF preservando o layout visual.
        """
        text = ""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                ext = page.extract_text(layout=True)
                if ext:
                    text += ext + "\n"
        return text
