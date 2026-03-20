import os
import tempfile
from typing import Any, Callable, Dict, Tuple

from src.models.constants import GEMINI_PROMPT_TEMPLATE, PROFISSIONAIS
from src.services.excel_service import ExcelService
from src.services.gemini_service import GeminiService
from src.services.google_sheets_service import GoogleSheetsService
from src.services.pdf_service import PdfService


class DocumentController:
    """
    Controlador responsável por orquestrar a extração de documentação.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.gemini_service = GeminiService(api_key=self.api_key)
        self.sheets_service = GoogleSheetsService()

    def process_single_pdf(
        self,
        pdf_file: Any,
        resp_selecionado: str,
        on_status: Callable[[str], None],
    ) -> Tuple[Dict[str, Any], bytes, str]:
        """
        Processa um único PDF: extrai texto, chama Gemini, gera Excel.

        Args:
            pdf_file: Arquivo PDF carregado (Streamlit UploadedFile).
            resp_selecionado: Nome do profissional responsável técnico selecionado.
            on_status: Callback para reportar progresso (recebe uma string de mensagem).

        Returns:
            Tupla (dados_extraidos, excel_bytes, nome_proponente).
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_file.seek(0)
            while True:
                chunk = pdf_file.read(64*1024)  # 64KB chunks
                if not chunk:
                    break
                tmp.write(chunk)
            tp = tmp.name

        try:
            on_status(f"📄 Extraindo layout visual de **{pdf_file.name}**...")
            pdf_service = PdfService(tp)
            md = pdf_service.get_text_with_layout()
        finally:
            if os.path.exists(tp):
                os.remove(tp)

        prompt = GEMINI_PROMPT_TEMPLATE.format(texto_laudo=md)

        on_status(f"🤖 Chamando Gemini para **{pdf_file.name}**...")
        dados = self.gemini_service.generate_content(prompt)

        excel_service = ExcelService(dados, resp_selecionado)
        excel_bytes, nome_proponente = excel_service.generate()

        return dados, excel_bytes, nome_proponente

    def sync_to_sheets(
        self, dados: Dict[str, Any], resp_selecionado: str
    ) -> Tuple[bool, str]:
        """
        Sincroniza os dados extraídos com o Google Sheets.

        Args:
            dados: Dados extraídos pelo Gemini.
            resp_selecionado: Nome do profissional responsável técnico selecionado.

        Returns:
            Tupla (sucesso, mensagem).
        """
        resp_nome = PROFISSIONAIS[resp_selecionado]["nome_resp"]
        return self.sheets_service.save(dados, resp_nome)
