import streamlit as st

# --- CARREGAMENTO DO AMBIENTE ---
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Extrator de Laudos", page_icon="🏛️", layout="centered")


def main() -> None:
    from src.views.main_view import render

    render()


if __name__ == "__main__":
    main()
