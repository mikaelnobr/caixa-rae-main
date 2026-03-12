import os
import re
from datetime import datetime
from typing import Any, Optional

from openpyxl.cell.cell import MergedCell


def get_secret(key: str) -> Optional[str]:
    """Busca chaves no secrets ou variáveis de ambiente, limpando aspas e espaços."""
    try:
        import streamlit as st

        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    val = os.getenv(key) or os.getenv(key.upper())
    if val:
        return val.strip().strip("'").strip('"')
    return None


def to_f(v: Any) -> float:
    """Converte qualquer valor para float de forma segura."""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    clean = re.sub(r"[^\d,.-]", "", str(v))
    if not clean:
        return 0.0
    try:
        return float(clean.replace(",", "."))
    except Exception:
        return 0.0


def calcular_serial_data(data_str: Optional[str]) -> int:
    """Calcula o serial da data conforme regra: (Ano - 2024) * 12 + Mês + 288."""
    try:
        if not data_str or "/" not in data_str:
            dt = datetime.now()
        else:
            dt = datetime.strptime(data_str.strip(), "%d/%m/%Y")

        return (dt.year - 2024) * 12 + dt.month + 288
    except Exception:
        dt = datetime.now()
        return (dt.year - 2024) * 12 + dt.month + 288


def safe_write(ws: Any, coord: str, val: Any) -> None:
    """Escreve um valor em uma célula do worksheet, tratando células mescladas."""
    try:
        if val is None:
            return

        cell = ws[coord]

        if isinstance(cell, MergedCell):
            for merged_range in ws.merged_cells.ranges:
                if coord in merged_range:
                    ws.cell(
                        row=merged_range.min_row, column=merged_range.min_col
                    ).value = val
                    return

        ws[coord].value = val
    except Exception:
        pass
