"""
Módulo de configurações constantes para o dashboard de produtividade.
"""

from typing import Dict, List  # Adicionei import
from datetime import datetime
# Configurações de metas
class MetaConfig:
    DIARIA: int = 8
    SEMANAL: int = 40

# Feriados por ano
FERIADOS: Dict[str, List[str]] = {
    '2024': [
        '2024-01-01', '2024-02-12', '2024-02-13', '2024-03-29',
        '2024-05-01', '2024-09-07', '2024-10-12', '2024-11-02',
        '2024-11-15', '2024-12-25'
    ],
    '2025': [
        '2025-01-01', '2025-02-12', '2025-02-13', '2025-03-29',
        '2025-05-01', '2025-09-07', '2025-10-12', '2025-11-02',
        '2025-11-15', '2025-12-25'
    ]
}

# Colunas obrigatórias para cada tipo de aba
COLUNAS_ORIGINAIS = {
    'data_fechamento': 'Date (Data Fechamento Operações)',
    'produtividade': 'QTD. PROXXIMA | Produtivas - Fechamento Geral',
    'protocolos': 'ID Protocolo | Proxxima',
    'tecnico': 'Nome Colaborador'
}
COLUNAS_OBRIGATORIAS = list(COLUNAS_ORIGINAIS.values())

def get_feriados_ano(ano: int = None) -> List[datetime]:
    """Retorna lista de feriados para o ano especificado ou atual."""
    ano = ano or datetime.now().year
    return [datetime.strptime(data, '%Y-%m-%d') for data in FERIADOS.get(str(ano), [])]