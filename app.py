"""
Dashboard de Produtividade - Ponto de Entrada Principal

Este módulo é o núcleo do sistema de análise de produtividade, responsável por:
- Coordenar o fluxo de processamento de dados
- Gerenciar a interface do usuário
- Integrar todos os componentes do sistema

Funcionalidades principais:
- Upload e validação de arquivos
- Processamento e análise de dados
- Visualização interativa de métricas
- Geração de insights acionáveis

Autor: [Juraci Junior]
Data: [28/06/2025]
Versão: 1.1.0
"""

import logging
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
import traceback

import pandas as pd
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from src.analysis import PerformanceAnalyzer
from src.config import get_feriados_ano, COLUNAS_OBRIGATORIAS, MetaConfig
from src.data_processing import DataProcessor
from src.visualization import DashboardVisualizer

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DashboardApp:
    """Classe principal que gerencia a aplicação do dashboard."""
    
    def __init__(self):
        self.processor: Optional[DataProcessor] = None
        self.analyzer: Optional[PerformanceAnalyzer] = None
        self.resumo: Optional[pd.DataFrame] = None
        self.feriados: pd.DataFrame = get_feriados_ano()
        
    def _validar_arquivo(self, uploaded_file: UploadedFile) -> bool:
        """Valida o arquivo carregado pelo usuário."""
        if not uploaded_file:
            st.warning("⚠️ Por favor, faça upload de um arquivo para continuar")
            return False
        
        if not uploaded_file.name.endswith('.xlsx'):
            st.error("❌ Formato inválido. Por favor, envie um arquivo Excel (.xlsx)")
            return False
            
        return True
    
    def _carregar_dados(self, uploaded_file: UploadedFile) -> bool:
        """Carrega e processa os dados do arquivo enviado."""
        try:
            with st.spinner("🔍 Validando estrutura do arquivo..."):
                self.processor = DataProcessor(uploaded_file, {})
                df_principal = self.processor.carregar_dados_principal()
                self.processor.validar_colunas(df_principal)
                
            with st.spinner("🔄 Processando dados..."):
                self.resumo = self.processor.preprocessar_dados(self.feriados)
                # Padronize os nomes das colunas para 'tecnico'
                self.resumo = self.resumo.rename(columns={
                    'Nome Colaborador': 'tecnico',
                    'Nome Técnico': 'tecnico'
                })
                self.analyzer = PerformanceAnalyzer(self.resumo, None, {})
                return True
                
        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}\n{traceback.format_exc()}")
            st.error(f"⛔ Falha crítica no processamento: {str(e)}")
            st.stop()
            return False
    
    def _gerar_modelo_dinamico(self) -> bytes:
        """Gera um DataFrame modelo em memória."""
        from io import BytesIO
        import pandas as pd

        try:
            # Tenta usar xlsxwriter, se não estiver disponível, usa openpyxl como fallback
            try:
                with pd.ExcelWriter(BytesIO(), engine='xlsxwriter'):
                    engine = 'xlsxwriter'
            except Exception:
                engine = 'openpyxl'

            # Crie um DataFrame com as colunas esperadas
            modelo = pd.DataFrame(columns=COLUNAS_OBRIGATORIAS)

            # Salve em memória
            output = BytesIO()
            with pd.ExcelWriter(output, engine=engine) as writer:
                modelo.to_excel(writer, index=False)
            return output.getvalue()
        except Exception as e:
            logger.error(f"Erro ao gerar modelo dinâmico: {str(e)}")
            raise RuntimeError("Não foi possível gerar o modelo. Verifique as dependências.")
    
    def _mostrar_secao_upload(self) -> Optional[UploadedFile]:
        """Exibe a seção de upload de arquivo."""
        st.markdown("""
        ## 📤 Carregamento de Dados

        Faça upload da planilha de produtividade para iniciar a análise.  
        O arquivo deve estar no formato Excel (.xlsx) e conter as colunas obrigatórias.
        """)

        col1, col2 = st.columns([3, 1])
        with col1:
            uploaded_file = st.file_uploader(
                "Selecione o arquivo de dados",
                type="xlsx",
                key="main_uploader",
                help="Planilha Excel contendo os dados de produtividade"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            try:
                # Tenta carregar o modelo do arquivo
                with open("templates/modelo_dados.xlsx", "rb") as f:
                    modelo_data = f.read()
            except FileNotFoundError:
                try:
                    # Se não encontrar, gera dinamicamente
                    st.warning("Modelo padrão não encontrado. Gerando modelo dinâmico...")
                    modelo_data = self._gerar_modelo_dinamico()
                    logger.info("Modelo dinâmico gerado com sucesso")
                except Exception as e:
                    st.error(f"Erro ao gerar modelo dinâmico: {str(e)}")
                    modelo_data = b""  # Define como vazio em caso de erro

            st.download_button(
                "Baixar Modelo",
                data=modelo_data,
                file_name="modelo_dados.xlsx",
                help="Baixe o template com a estrutura esperada"
            )

        return uploaded_file if self._validar_arquivo(uploaded_file) else None
    
    def _mostrar_secao_analise_geral(self):
        """Exibe a seção de análise geral."""
        with st.expander("📈 VISÃO GERAL DE PRODUTIVIDADE", expanded=True):
            tabs = st.tabs(["📊 Resumo", "📌 Principais Métricas", "🔄 Evolução Temporal"])
            
            with tabs[0]:
                DashboardVisualizer.mostrar_ranking_consistencia(self.resumo)
                
            with tabs[1]:
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_tecnicos = self.resumo['tecnico'].nunique()
                    st.metric("Técnicos Analisados", total_tecnicos)
                with col2:
                    semanas = self.resumo['semana'].nunique()
                    st.metric("Semanas Analisadas", semanas)
                with col3:
                    meta_media = self.resumo['meta_batida'].mean() * 100
                    st.metric("Meta Média Batida", f"{meta_media:.1f}%")
                
                st.markdown("---")
                DashboardVisualizer.mostrar_streaks(self.resumo)
                
                
            with tabs[2]:
                DashboardVisualizer.mostrar_evolucao_produtividade(self.resumo)
    
    def _mostrar_secao_tecnicos(self):
        """Exibe a seção de análise por técnico."""
        with st.expander("👷 ANÁLISE POR TÉCNICO", expanded=True):
            tecnico_selecionado = st.selectbox(
                "Selecione um técnico para análise detalhada:",
                self.resumo['tecnico'].unique(),
                key="tecnico_selectbox",
                help="Selecione um técnico para visualizar análises específicas"
            )
            
            if tecnico_selecionado:
                with st.spinner(f"🔍 Analisando desempenho de {tecnico_selecionado}..."):
                    df_tendencia = self.resumo.rename(columns={
                        'tecnico': 'Nome Colaborador',
                        'semana': 'Semana',
                        'meta_batida': 'Meta Batida',
                        'produtividade': 'QTD. PROXXIMA | Produtivas - Fechamento Geral'
                    })
                    analyzer = PerformanceAnalyzer(df_tendencia, None, {})
                    analise_tendencia = analyzer.identificar_tendencia(tecnico_selecionado)
                    DashboardVisualizer.mostrar_tendencia_tecnico(analise_tendencia)
                    
                    tabs = st.tabs(["📋 Desempenho", "📅 Histórico", "📊 Comparativo"])
                    
                    with tabs[0]:
                        dados_tecnico = self.resumo[self.resumo['tecnico'] == tecnico_selecionado]
                        st.dataframe(
                            dados_tecnico.style
                            .background_gradient(subset=['produtividade'], cmap='YlGnBu')
                            .format({'produtividade': "{:.1f}"}),
                            height=300
                        )
                    
                    with tabs[1]:
                        fig = px.line(
                            dados_tecnico,
                            x='semana',
                            y='produtividade',
                            title=f"Evolução de Produtividade - {tecnico_selecionado}",
                            markers=True
                        )
                        fig.add_hline(y=MetaConfig.SEMANAL, line_dash="dash", line_color="red")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with tabs[2]:
                        media_geral = self.resumo['produtividade'].mean()
                        media_tecnico = dados_tecnico['produtividade'].mean()
                        
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            x=['Média Geral', 'Média do Técnico'],
                            y=[media_geral, media_tecnico],
                            marker_color=[DashboardVisualizer.COLORS['primary'], DashboardVisualizer.COLORS['success']]
                        ))
                        fig.add_hline(y=MetaConfig.SEMANAL, line_dash="dash", line_color="red")
                        st.plotly_chart(fig, use_container_width=True)
    
    def _mostrar_secao_insights(self):
        """Exibe a seção de insights automatizados."""
        with st.expander("🧠 INSIGHTS E RECOMENDAÇÕES", expanded=True):
            alertas = self.analyzer.gerar_alertas()
            DashboardVisualizer.mostrar_alertas(alertas)
            
            st.markdown("---")
            st.subheader("🔍 Padrões Identificados")
            
            tabs = st.tabs(["📉 Queda", "🔄 Oscilação", "📈 Crescimento"])
            
            with tabs[0]:
                DashboardVisualizer.mostrar_padroes_desempenho(self.resumo)
            
    
    def run(self):
        """Método principal para executar a aplicação."""
        try:
            DashboardVisualizer.configurar_layout()
            
            # Seção de upload de dados
            uploaded_file = self._mostrar_secao_upload()
            if not uploaded_file:
                return
                
            # Processamento dos dados
            if not self._carregar_dados(uploaded_file):
                return
                
            # Seções de análise
            self._mostrar_secao_analise_geral()
            self._mostrar_secao_tecnicos()
            self._mostrar_secao_insights()
            
            # Rodapé
            st.markdown("---")
            st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
        except Exception as e:
            logger.error(f"Erro na execução do dashboard: {str(e)}\n{traceback.format_exc()}")
            st.error("⛔ Ocorreu um erro crítico na aplicação. Por favor, contate o suporte.")
            st.stop()

def main():
    """Ponto de entrada principal da aplicação."""
    app = DashboardApp()
    app.run()

if __name__ == "__main__":
    main()