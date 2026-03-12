from io import BytesIO
from typing import Any, Dict, Tuple

from openpyxl import Workbook

from src.models.constants import PROFISSIONAIS
from src.services.utils_service import to_f


def generate_excel(dados: Dict[str, Any], resp_selecionado: str) -> Tuple[bytes, str]:
    """Gera um arquivo Excel DADOS_IA a partir dos dados extraídos pelo Gemini.

    Retorna (excel_bytes, nome_base_proponente).
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "DADOS_IA"

    p = PROFISSIONAIS[resp_selecionado]

    mapa = [
        ("proponente", str(dados.get("proponente", "")).upper()),
        ("cpf_cnpj", str(dados.get("cpf_cnpj", ""))),
        ("ddd", str(dados.get("ddd", ""))),
        ("telefone", str(dados.get("telefone", ""))),
        ("endereco_literal", str(dados.get("endereco_literal", "")).upper()),
        ("coordenada_s", str(dados.get("coordenada_s", ""))),
        ("coordenada_w", str(dados.get("coordenada_w", ""))),
        ("complemento", str(dados.get("complemento", "")).upper()),
        ("bairro", str(dados.get("bairro", "")).upper()),
        ("cep", str(dados.get("cep", ""))),
        ("municipio", str(dados.get("municipio", "")).upper()),
        ("uf", str(dados.get("uf", ""))),
        ("valor_terreno", to_f(dados.get("valor_terreno", 0))),
        ("matricula", str(dados.get("matricula", ""))),
        ("oficio", str(dados.get("oficio", ""))),
        ("comarca", str(dados.get("comarca", ""))),
        ("uf_matricula", str(dados.get("uf_matricula", ""))),
        ("categoria", "Casa"),
        ("uso", "Residencial"),
        ("finalidade_vistoria", "Vistoria para aferição de obra"),
        ("valor_imovel", to_f(dados.get("valor_imovel", 0))),
        ("numero_etapas", to_f(dados.get("numero_etapas", 0))),
        ("empresa", p["empresa"].upper()),
        ("cnpj", p["cnpj"]),
        ("cpf_empresa", p["cpf_emp"]),
        ("nome_responsavel", p["nome_resp"].upper()),
        ("cpf_responsavel", p["cpf_resp"]),
        ("registro", p["registro"].upper()),
    ]

    for row_idx, (rotulo, valor) in enumerate(mapa, start=1):
        ws.cell(row=row_idx, column=1, value=rotulo)
        ws.cell(row=row_idx, column=2, value=valor)

    # --- INCIDÊNCIAS (20 valores) mescladas em 3 colunas ---
    incs = dados.get("incidencias", [])
    for i in range(20):
        row = i + 1
        ws.cell(row=row, column=3, value=f"incidencia_{i + 1}")
        ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=6)
        ws.cell(row=row, column=4, value=to_f(incs[i]) if i < len(incs) else 0.0)

    # --- ACUMULADO PROPOSTO (até 37 valores) mesclado em 3 colunas ---
    ap = dados.get("acumulado_proposto", [])
    stop = False
    for i in range(37):
        row = i + 1
        ws.cell(row=row, column=7, value=f"acumulado_{i}")
        ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=10)
        if not stop and i < len(ap):
            v = to_f(ap[i])
            ws.cell(row=row, column=8, value=v)
            if v >= 100:
                stop = True
        else:
            ws.cell(row=row, column=8, value=None)

    out = BytesIO()
    wb.save(out)

    proponente_str = str(dados.get("proponente", "")).strip()
    primeiro_nome = proponente_str.split()[0].upper() if proponente_str else "LAUDO"
    return out.getvalue(), primeiro_nome
