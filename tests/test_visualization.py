"""
Testes para o módulo de visualização.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import streamlit as st
from src.visualization import DashboardVisualizer

@pytest.fixture
def sample_resumo():
    """DataFrame de resumo para testes de visualização."""
    datas = [datetime(2024, 1, 1) + timedelta(weeks=i) for i in range(4)]
    return pd.DataFrame({
        'Nome Colaborador': ['Técnico 1']*4 + ['Técnico 2']*4,
        'Semana': datas*2,
        'Pontuação': [10, 12, 8, 15, 5, 6, 7, 4],
        'Meta Semana': [40]*8,
        'Meta Batida': [False]*8,
        'Atendimentos': [5]*8
    })

@pytest.fixture
def sample_analise_tendencia():
    """Dicionário de análise de tendência para testes."""
    return {
        'status': 'ok',
        'tendencia': 'alta',
        'coeficiente': 1.5,
        'projecao': 42.0
    }

@pytest.fixture
def sample_alertas():
    """Lista de alertas para testes."""
    return [
        {
            'tipo': 'queda_performance',
            'tecnico': 'Técnico 1',
            'severidade': 'alta',
            'message': 'Queda de performance detectada'
        },
        {
            'tipo': 'bairro_problematico',
            'bairro': 'Centro',
            'severidade': 'media',
            'message': 'Bairro com baixa produtividade'
        }
    ]

def test_configurar_layout(monkeypatch):
    """Testa a configuração do layout."""
    mock_set_page_config = MagicMock()
    monkeypatch.setattr(st, "set_page_config", mock_set_page_config)
    monkeypatch.setattr(st, "title", MagicMock())
    
    DashboardVisualizer.configurar_layout()
    
    mock_set_page_config.assert_called_once_with(
        page_title="📊 Dashboard Unificado",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def test_mostrar_ranking_consistencia(sample_resumo, monkeypatch):
    """Testa a exibição do ranking de consistência."""
    # Mock das funções do Streamlit
    monkeypatch.setattr(st, "subheader", MagicMock())
    monkeypatch.setattr(st, "dataframe", MagicMock())
    monkeypatch.setattr(st, "plotly_chart", MagicMock())
    
    ranking = DashboardVisualizer.mostrar_ranking_consistencia(sample_resumo)
    
    assert isinstance(ranking, pd.DataFrame)
    assert 'Percentual_Metas_Batidas' in ranking.columns
    st.subheader.assert_called_once_with("🏆 Ranking de Consistência")
    assert st.dataframe.called
    assert st.plotly_chart.called

def test_mostrar_tendencia_tecnico(sample_analise_tendencia, monkeypatch):
    """Testa a exibição da análise de tendência."""
    # Mock das funções do Streamlit
    monkeypatch.setattr(st, "subheader", MagicMock())
    monkeypatch.setattr(st, "columns", lambda: (MagicMock(), MagicMock()))
    monkeypatch.setattr(st, "metric", MagicMock())
    monkeypatch.setattr(st, "warning", MagicMock())
    
    # Teste com análise válida
    DashboardVisualizer.mostrar_tendencia_tecnico(sample_analise_tendencia)
    st.subheader.assert_called_once_with("📈 Análise de Tendência")
    assert st.metric.call_count == 2
    
    # Teste com análise inválida
    DashboardVisualizer.mostrar_tendencia_tecnico({'status': 'insuficiente'})
    st.warning.assert_called_once_with("Dados insuficientes para análise de tendência")

def test_mostrar_alertas(sample_alertas, monkeypatch):
    """Testa a exibição de alertas."""
    # Mock das funções do Streamlit
    monkeypatch.setattr(st, "subheader", MagicMock())
    monkeypatch.setattr(st, "error", MagicMock())
    monkeypatch.setattr(st, "warning", MagicMock())
    monkeypatch.setattr(st, "info", MagicMock())
    monkeypatch.setattr(st, "success", MagicMock())
    
    # Teste com alertas
    DashboardVisualizer.mostrar_alertas(sample_alertas)
    st.subheader.assert_called_once_with("🚨 Alertas Importantes")
    assert st.error.called
    assert st.warning.called
    
    # Teste sem alertas
    DashboardVisualizer.mostrar_alertas([])
    st.success.assert_called_once_with("✅ Nenhum alerta crítico identificado")

def test_mostrar_alertas_diversos_tipos(monkeypatch):
    """Testa a exibição de diferentes tipos de alertas."""
    # Mock das funções do Streamlit
    monkeypatch.setattr(st, "subheader", MagicMock())
    monkeypatch.setattr(st, "error", MagicMock())
    monkeypatch.setattr(st, "warning", MagicMock())
    monkeypatch.setattr(st, "info", MagicMock())
    
    alertas = [
        {'tipo': 'tipo1', 'severidade': 'alta', 'message': 'Mensagem 1'},
        {'tipo': 'tipo2', 'severidade': 'media', 'message': 'Mensagem 2'},
        {'tipo': 'tipo3', 'severidade': 'baixa', 'message': 'Mensagem 3'}
    ]
    
    DashboardVisualizer.mostrar_alertas(alertas)
    
    assert st.error.called
    assert st.warning.called
    assert st.info.called