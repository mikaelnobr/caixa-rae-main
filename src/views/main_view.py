import gc
import zipfile
from io import BytesIO

import streamlit as st

from src.controllers.document_controller import DocumentController
from src.models.constants import PROFISSIONAIS


class MainView:
    """
    Classe responsável por renderizar a interface principal da aplicação.
    """

    def __init__(self):
        if "processed" not in st.session_state:
            st.session_state["processed"] = False
        self.api_key = ""
        self.resp_selecionado = ""

    def render_sidebar(self) -> None:
        """
        Renderiza a barra lateral de configurações.
        """
        with st.sidebar:
            st.header("⚙️ Configurações")
            self.api_key = st.text_input("Gemini API Key:", type="password")

            resp_selecionado_raw = st.selectbox(
                "Responsável Técnico:", options=list(PROFISSIONAIS.keys())
            )
            self.resp_selecionado = (
                str(resp_selecionado_raw) if resp_selecionado_raw else ""
            )

            if st.session_state.get("processed", False):
                if st.button("🔄 NOVA FILA"):
                    st.session_state["processed"] = False
                    st.rerun()

    def render_previous_results(self) -> None:
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
            if res.get("download_bytes"):
                label = (
                    "📥 BAIXAR PLANILHA (.xlsx)"
                    if res["download_mime"] != "application/zip"
                    else "📥 BAIXAR TODOS OS LAUDOS PROCESSADOS (.zip)"
                )
                st.download_button(
                    label,
                    res["download_bytes"],
                    res["download_name"],
                    res["download_mime"],
                )
            if res.get("erros"):
                with st.expander("⚠️ Laudos com Erro"):
                    for err in res["erros"]:
                        st.warning(err)

    def render_upload_and_processing(self) -> None:
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
            if not self.api_key or not pdf_files:
                st.warning("Preencha a API Key e selecione ao menos 1 PDF.")
                return

            if len(pdf_files) > 20:
                st.warning("⚠️ Limite máximo de 20 laudos por lote excedido. Por favor, divida o lote e tente novamente.")
                return
            
            total_size_bytes = sum(pdf.size for pdf in pdf_files)
            if total_size_bytes > 100 * 1024 * 1024:
                st.warning(f"⚠️ O tamanho total dos arquivos ({total_size_bytes / (1024*1024):.1f} MB) excede o limite de 100 MB. Por favor, divida o lote.")
                return

            total = len(pdf_files)
            status_container = st.status(
                f"🚀 Processando {total} laudo(s)...", expanded=True
            )
            resultados_excel = []
            erros = []
            ok_count = 0

            doc_controller = DocumentController(api_key=self.api_key)

            try:
                # Chamada batch: extrai todos os textos e faz 1 chamada Gemini
                batch_results = doc_controller.process_batch(
                    pdf_files,
                    self.resp_selecionado,
                    on_status=lambda msg: status_container.write(msg),
                )

                # Processar resultados individuais (sync Sheets + coleta Excel)
                for idx, (dados, excel_bytes, nome_proponente) in enumerate(
                    batch_results
                ):
                    pdf = pdf_files[idx]
                    status_container.write(
                        f"☁️ Sincronizando **{pdf.name}** com Google Sheets..."
                    )

                    sheets_ok, sheets_msg = doc_controller.sync_to_sheets(
                        dados, self.resp_selecionado
                    )
                    if not sheets_ok:
                        status_container.write(
                            f"⚠️ Google Sheets ({pdf.name}): {sheets_msg}"
                        )
                    else:
                        status_container.write(f"✅ {pdf.name}: {sheets_msg}")

                    if gerar_excel:
                        resultados_excel.append(
                            (f"RAE_{nome_proponente}.xlsx", excel_bytes)
                        )
                    ok_count += 1

                status_container.update(
                    label=f"✅ {ok_count}/{total} laudos processados com sucesso!",
                    state="complete",
                )

            except Exception as e:
                erros.append(f"❌ Erro no processamento em lote: {e}")
                status_container.update(
                    label="❌ Erro no processamento",
                    state="error",
                )

            gc.collect()

            # Empacotar em ZIP Somente se for mais de uma planilha
            download_bytes = None
            download_name = ""
            download_mime = ""

            if len(resultados_excel) > 1:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for nome, dados_xl in resultados_excel:
                        zf.writestr(nome, dados_xl)
                download_bytes = zip_buffer.getvalue()
                download_name = "LAUDOS_processados.zip"
                download_mime = "application/zip"
            elif len(resultados_excel) == 1:
                download_name, download_bytes = resultados_excel[0]
                download_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            st.session_state["batch_results"] = {
                "ok": ok_count,
                "fail": len(erros),
                "total": total,
                "download_bytes": download_bytes,
                "download_name": download_name,
                "download_mime": download_mime,
                "erros": erros,
            }
            st.session_state["processed"] = True
            gc.collect()
            st.rerun()


    def render(self) -> None:
        """
        Renderiza a interface principal da aplicação.
        """
        st.title("🏛️ Extrator de Laudo")

        self.render_sidebar()

        if st.session_state["processed"]:
            self.render_previous_results()
            return

        self.render_upload_and_processing()
