"""
Testes para o módulo de análise.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.analysis import PerformanceAnalyzer

@pytest.fixture
def sample_resumo():
    """DataFrame de resumo para testes."""
    datas = [datetime(2024, 1, 1) + timedelta(weeks=i) for i in range(4)]
    return pd.DataFrame({
        'Nome Colaborador': ['Técnico 1']*4 + ['Técnico 2']*4,
        'Semana': datas*2,
        'Pontuação': [10, 12, 8, 15, 5, 6, 7, 4],
        'Meta Semana': [40]*8,
        'Meta Batida': [False]*8
    })

def test_identificar_tendencia(sample_resumo):
    """Testa identificação de tendência."""
    analyzer = PerformanceAnalyzer(sample_resumo, None, {})
    analise = analyzer.identificar_tendencia('Técnico 1')
    assert analise['status'] == 'ok'
    assert analise['tendencia'] in ['alta', 'baixa', 'estavel']

def test_gerar_alertas(sample_resumo):
    """Testa geração de alertas."""
    analyzer = PerformanceAnalyzer(sample_resumo, None, {})
    alertas = analyzer.gerar_alertas()
    assert isinstance(alertas, list)

def test_prever_meta_proxima_semana(sample_resumo):
    """Testa previsão de meta."""
    analyzer = PerformanceAnalyzer(sample_resumo, None, {})
    previsao = analyzer.prever_meta_proxima_semana('Técnico 1')
    assert previsao['status'] == 'ok'
    assert isinstance(previsao['previsao'], float)