import os
import tempfile
from typing import Any, Callable, Dict, Tuple

from src.models.constants import GEMINI_PROMPT_TEMPLATE, PROFISSIONAIS
from src.services.excel_service import generate_excel
from src.services.gemini_service import call_gemini
from src.services.google_sheets_service import save_to_google_sheets
from src.services.pdf_service import get_text_with_layout


def process_single_pdf(
    pdf_file: Any,
    api_key: str,
    resp_selecionado: str,
    on_status: Callable[[str], None],
) -> Tuple[Dict[str, Any], bytes, str]:
    """Processa um único PDF: extrai texto, chama Gemini, gera Excel.

    Args:
        pdf_file: Arquivo PDF carregado (Streamlit UploadedFile).
        api_key: Chave da API Gemini.
        resp_selecionado: Nome do profissional responsável técnico selecionado.
        on_status: Callback para reportar progresso (recebe uma string de mensagem).

    Returns:
        Tupla (dados_extraidos, excel_bytes, primeiro_nome).
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.getbuffer())
        tp = tmp.name
    try:
        on_status(f"📄 Extraindo layout visual de **{pdf_file.name}**...")
        md = get_text_with_layout(tp)
    finally:
        if os.path.exists(tp):
            os.remove(tp)

    prompt = GEMINI_PROMPT_TEMPLATE.format(texto_laudo=md)

    on_status(f"🤖 Chamando Gemini para **{pdf_file.name}**...")
    dados = call_gemini(api_key, prompt)

    excel_bytes, primeiro_nome = generate_excel(dados, resp_selecionado)

    return dados, excel_bytes, primeiro_nome


def sync_to_sheets(
    dados: Dict[str, Any], resp_selecionado: str
) -> Tuple[bool, str]:
    """Sincroniza os dados extraídos com o Google Sheets.

    Args:
        dados: Dados extraídos pelo Gemini.
        resp_selecionado: Nome do profissional responsável técnico selecionado.

    Returns:
        Tupla (sucesso, mensagem).
    """
    resp_nome = PROFISSIONAIS[resp_selecionado]["nome_resp"]
    return save_to_google_sheets(dados, resp_nome)
