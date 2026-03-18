import gc
import zipfile
from io import BytesIO

import streamlit as st

from src.controllers.document_controller import process_single_pdf, sync_to_sheets
from src.models.constants import PROFISSIONAIS


def render_sidebar() -> tuple[str, str]:
    """
    Renderiza a barra lateral de configurações.
    """
    with st.sidebar:
        st.header("⚙️ Configurações")
        api_key = st.text_input("Gemini API Key:", type="password")
        
        resp_selecionado_raw = st.selectbox(
            "Responsável Técnico:", options=list(PROFISSIONAIS.keys())
        )
        resp_selecionado = str(resp_selecionado_raw) if resp_selecionado_raw else ""
        
        if st.session_state.get("processed", False):
            if st.button("🔄 NOVA FILA"):
                st.session_state["processed"] = False
                st.rerun()

    return api_key, resp_selecionado


def render_previous_results() -> None:
    """
    Renderiza na tela os resultados do processamento anterior, se houver.
    Permite o download do zip e visualização de erros.
    """
    st.success("✅ Processamento Concluído!")
    if "batch_results" in st.session_state:
        res = st.session_state["batch_results"]
        st.info(
            f"📊 **{res['ok']}** laudos processados com sucesso, "
            f"**{res['fail']}** falharam de **{res['total']}** total."
        )
        if res.get("zip_bytes"):
            st.download_button(
                "📥 BAIXAR TODOS OS LAUDOS PROCESSADOS (.zip)",
                res["zip_bytes"],
                "LAUDOS_processados.zip",
                "application/zip",
            )
        if res.get("erros"):
            with st.expander("⚠️ Laudos com Erro"):
                for err in res["erros"]:
                    st.warning(err)


def render_upload_and_processing(api_key: str, resp_selecionado: str) -> None:
    """
    Renderiza a área de upload de PDFs, gerencia o fluxo de processamento e 
    atualiza o progresso na tela iterando sobre a lista de arquivos.
    """
    pdf_files = st.file_uploader(
        "📄 Laudos Técnicos (PDFs)", type=["pdf"], accept_multiple_files=True
    )
    gerar_excel = st.checkbox(
        "📊 Gerar arquivo DADOS_IA para preencher a RAE?", value=True
    )

    if pdf_files:
        st.caption(f"📁 {len(pdf_files)} laudo(s) selecionado(s)")

    if st.button("🚀 INICIAR PROCESSAMENTO"):
        if not api_key or not pdf_files:
            st.warning("Preencha a API Key e selecione ao menos 1 PDF.")
            return

        total = len(pdf_files)
        progress_bar = st.progress(
            0, text=f"Iniciando processamento de {total} laudo(s)..."
        )
        resultados_excel = []
        erros = []
        ok_count = 0

        for idx, pdf in enumerate(pdf_files):
            progress_bar.progress(
                (idx) / total,
                text=f"📄 Processando {idx + 1}/{total}: {pdf.name}",
            )
            status_container = st.status(
                f"[{idx + 1}/{total}] {pdf.name}",
                expanded=(idx == len(pdf_files) - 1),
            )
            try:
                dados, excel_bytes, primeiro_nome = process_single_pdf(
                    pdf,
                    api_key,
                    resp_selecionado,
                    on_status=lambda msg: status_container.write(msg),
                )

                sheets_ok, sheets_msg = sync_to_sheets(dados, resp_selecionado)
                if not sheets_ok:
                    status_container.write(f"⚠️ Google Sheets: {sheets_msg}")
                else:
                    status_container.write(f"✅ {sheets_msg}")

                if gerar_excel:
                    resultados_excel.append(
                        (f"RAE_{primeiro_nome}.xlsx", excel_bytes)
                    )

                status_container.update(
                    label=f"✅ [{idx + 1}/{total}] {pdf.name}",
                    state="complete",
                )
                ok_count += 1

            except Exception as e:
                erros.append(f"❌ {pdf.name}: {e}")
                status_container.update(
                    label=f"❌ [{idx + 1}/{total}] {pdf.name}",
                    state="error",
                )

            gc.collect()

        progress_bar.progress(
            1.0, text=f"✅ Concluído! {ok_count}/{total} laudos processados e salvos no Google Sheets."
        )

        # Empacotar todos os Excel em ZIP
        zip_bytes = None
        if resultados_excel:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for nome, dados_xl in resultados_excel:
                    zf.writestr(nome, dados_xl)
            zip_bytes = zip_buffer.getvalue()

        st.session_state["batch_results"] = {
            "ok": ok_count,
            "fail": len(erros),
            "total": total,
            "zip_bytes": zip_bytes,
            "erros": erros,
        }
        st.session_state["processed"] = True
        gc.collect()
        st.rerun()


def render() -> None:
    """
    Renderiza a interface principal da aplicação.
    """
    st.title("🏛️ Extrator de Laudo")

    if "processed" not in st.session_state:
        st.session_state["processed"] = False

    api_key, resp_selecionado = render_sidebar()

    if st.session_state["processed"]:
        render_previous_results()
        return

    render_upload_and_processing(api_key, resp_selecionado)
