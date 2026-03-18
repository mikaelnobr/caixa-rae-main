import streamlit as st

# --- CARREGAMENTO DO AMBIENTE ---
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(
    page_title="Extrator de Laudos", page_icon="🏛️", layout="centered"
)

# --- VERIFICAÇÃO DE DEPENDÊNCIAS ---
try:
    import pdfplumber
    import google.genai
    import gspread
    from google.oauth2.service_account import Credentials

    DEPENDENCIAS_OK = True
except ImportError as e:
    DEPENDENCIAS_OK = False
    ERRO_IMPORT = str(e)


def main() -> None:
    if not DEPENDENCIAS_OK:
        st.error(f"Erro: {ERRO_IMPORT}")
        return

    from src.views.main_view import render

    render()


if __name__ == "__main__":
    main()
