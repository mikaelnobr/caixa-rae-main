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
    try:
        from src.views.main_view import MainView
    except ImportError as e:
        st.error(
            "🛑 **Erro Crítico de Inicialização**\n\n"
            f"O sistema não conseguiu carregar uma ou mais dependências locais.\n\n"
            f"**Detalhes do Erro:** `{e}`\n\n"
            "Verifique se o seu ambiente virtual está ativado e todos os pacotes definidos no arquivo `requirements.txt` foram instalados com sucesso."
        )
        st.stop()
        return

    view = MainView()
    view.render()


if __name__ == "__main__":
    main()
