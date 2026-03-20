import json
import os
from typing import Any, Dict, Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials

from src.services.utils_service import UtilsService


class GoogleSheetsService:
    """
    Serviço para sincronização de dados com o Google Sheets.
    """
    def __init__(self):
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        self.client = self._authenticate()

    def _authenticate(self) -> Optional[Any]:
        """
        Autentica e retorna um cliente gspread.
        """
        if os.path.exists("service_account.json"):
            try:
                return gspread.authorize(
                    Credentials.from_service_account_file(
                        "service_account.json", scopes=self.scopes
                    )
                )
            except Exception:
                pass
        
        json_str = UtilsService.get_secret("GCP_SERVICE_ACCOUNT")
        if json_str:
            try:
                clean_str = json_str.strip().replace("\\\\n", "\n").replace("\\n", "\n")
                info = json.loads(clean_str, strict=False)
                if "private_key" in info:
                    info["private_key"] = info["private_key"].replace("\\n", "\n")
                return gspread.authorize(
                    Credentials.from_service_account_info(info, scopes=self.scopes)
                )
            except Exception:
                pass
        return None

    def _prepare_row_data(self, dados_ia: Dict[str, Any], resp_nome: str) -> list:
        tel = f"({dados_ia.get('ddd', '')}) {dados_ia.get('telefone', '')}"
        val_data_evento = UtilsService.calcular_serial_data(dados_ia.get("data_referencia", ""))

        v_terreno = UtilsService.to_f(dados_ia.get("valor_terreno", 0))
        a_terreno = UtilsService.to_f(dados_ia.get("area_terreno", 0))
        v_unit_terreno = round(v_terreno / a_terreno, 2) if a_terreno > 0 else 0

        endereco_literal = str(dados_ia.get("endereco_literal", "")).upper()

        return [
            str(dados_ia.get("empresa_responsavel", "")).upper(),
            str(resp_nome).upper(),
            str(dados_ia.get("proponente", "")).upper(),
            tel,
            endereco_literal,
            str(dados_ia.get("bairro", "")).upper(),
            str(dados_ia.get("municipio", "")).upper(),
            UtilsService.dmstodecimal(dados_ia.get("coordenada_s", "")),
            UtilsService.dmstodecimal(dados_ia.get("coordenada_w", "")),
            a_terreno,
            UtilsService.to_f(dados_ia.get("area_construida", 0)),
            UtilsService.to_f(dados_ia.get("quartos", 0)),
            UtilsService.to_f(dados_ia.get("banheiros", 0)),
            UtilsService.to_f(dados_ia.get("suites", 0)),
            UtilsService.to_f(dados_ia.get("vagas", 0)),
            UtilsService.to_f(dados_ia.get("valor_imovel", 0)),
            UtilsService.to_f(dados_ia.get("valor_unitario", 0)),
            str(dados_ia.get("padrao_acabamento", "")).upper(),
            str(dados_ia.get("estado_conservacao", "")).upper(),
            str(dados_ia.get("infraestrutura", "")).upper(),
            str(dados_ia.get("servicos_publicos", "")).upper(),
            str(dados_ia.get("usos_predominantes", "")).upper(),
            str(dados_ia.get("via_acesso", "")).upper(),
            str(dados_ia.get("regiao_contexto", "")).upper(),
            str(dados_ia.get("idade_estimada", "")),
            val_data_evento,
            # --- BLOCO TERRENO (Repetidos conforme planilha) ---
            str(dados_ia.get("proponente", "")).upper(),
            tel,
            endereco_literal,
            str(dados_ia.get("municipio", "")).upper(),
            str(dados_ia.get("bairro", "")).upper(),
            UtilsService.dmstodecimal(dados_ia.get("coordenada_s", "")),
            UtilsService.dmstodecimal(dados_ia.get("coordenada_w", "")),
            a_terreno,
            UtilsService.to_f(dados_ia.get("testada", 0)),
            v_terreno,
            v_unit_terreno,
            str(dados_ia.get("infraestrutura", "")).upper(),
            str(dados_ia.get("servicos_publicos", "")).upper(),
            str(dados_ia.get("usos_predominantes", "")).upper(),
            str(dados_ia.get("via_acesso", "")).upper(),
            str(dados_ia.get("regiao_contexto", "")).upper(),
            val_data_evento,
        ]

    def save(self, dados_ia: Dict[str, Any], resp_nome: str) -> Tuple[bool, str]:
        """
        Sincroniza os dados extraídos com o Google Sheets (43 colunas).
        """
        try:
            if not self.client:
                return (
                    False,
                    "Falha na autenticação do Google Sheets (service_account.json faltando ou inválido).",
                )

            sheet_id = UtilsService.get_secret("GOOGLE_SHEET_ID")
            if not sheet_id:
                return (
                    False,
                    "A configuração GOOGLE_SHEET_ID não foi encontrada (adicione no .env ou st.secrets).",
                )

            sheet = self.client.open_by_key(sheet_id).get_worksheet(0)
            row = self._prepare_row_data(dados_ia, resp_nome)
            sheet.append_row(row)
            return True, "Salvo com sucesso no Google Sheets!"
        except Exception as e:
            return False, f"Erro ao salvar no Google Sheets: {e}"
