"""
Testes para o módulo de processamento de dados.
"""

import pytest
import pandas as pd
from datetime import datetime
from src.data_processing import DataProcessor
from src.config import COLUNAS_OBRIGATORIAS

@pytest.fixture
def sample_data():
    """DataFrame de exemplo para testes."""
    return pd.DataFrame({
        'Date (Data Fechamento Operações)': ['2024-01-01', '2024-01-02'],
        'Nome Colaborador': ['Técnico 1', 'Técnico 2'],
        'QTD. PROXXIMA | Produtivas - Fechamento Geral': [10, 8],
        'ID Protocolo | Proxxima': [1, 1]
    })

@pytest.fixture
def sample_feriados():
    """Lista de feriados para testes."""
    return [datetime(2024, 1, 1)]

def test_validar_colunas(sample_data):
    """Testa a validação de colunas obrigatórias."""
    processor = DataProcessor(None, {})
    assert processor.validar_colunas(sample_data, 'principal') == True

def test_validar_colunas_faltantes(sample_data):
    """Testa detecção de colunas faltantes."""
    processor = DataProcessor(None, {})
    with pytest.raises(ValueError):
        processor.validar_colunas(sample_data.drop(columns=['Nome Colaborador']), 'principal')

def test_calcular_meta(sample_feriados):
    """Testa cálculo de meta semanal."""
    processor = DataProcessor(None, {})
    semana = datetime(2024, 1, 1)  # Segunda-feira com feriado na segunda
    assert processor.calcular_meta(semana, sample_feriados) == 32  # 40 - 8

def test_preprocessar_dados(sample_data, sample_feriados):
    """Testa o pré-processamento básico dos dados."""
    processor = DataProcessor(None, {})
    processor.df_principal = sample_data
    resumo = processor.preprocessar_dados(sample_feriados)
    
    assert 'Semana' in resumo.columns
    assert 'Meta Semana' in resumo.columns
    assert 'Meta Batida' in resumo.columns