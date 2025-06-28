"""
Módulo de Visualização de Dados para Dashboard de Produtividade

Este módulo fornece uma classe abrangente para visualização de métricas de produtividade,
com gráficos interativos, alertas e análises de tendência usando Streamlit e Plotly.

Recursos principais:
- Visualização de ranking de consistência
- Análise de sequências de metas (streaks)
- Identificação de padrões de desempenho
- Gráficos evolutivos de produtividade
- Alertas personalizados por severidade
- Análise de tendência e projeções

Autor: [Juraci Junior]
Data: [28/06/2025]
Versão: 1.1.0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from src.config import MetaConfig
import numpy as np

class DashboardVisualizer:
    """Classe responsável por todas as visualizações do dashboard de produtividade.
    
    Utiliza Streamlit para layout e Plotly para gráficos interativos, proporcionando
    uma experiência rica em dados com análises detalhadas de desempenho individual
    e coletivo.
    """
    
    # Configurações de estilo
    COLORS = {
        'success': '#2ecc71',
        'warning': '#f39c12',
        'danger': '#e74c3c',
        'info': '#3498db',
        'primary': '#2980b9'
    }
    
    @staticmethod
    def configurar_layout() -> None:
        """Configura o layout básico do dashboard com Streamlit."""
        st.set_page_config(
            page_title="📊 Dashboard de Produtividade - Análise Avançada", 
            layout="wide",
            initial_sidebar_state="expanded",
            page_icon="📈"
        )
        
        # CSS customizado para melhorar a aparência
        st.markdown(f"""
        <style>
            .reportview-container .main .block-container{{
                padding-top: 2rem;
                padding-bottom: 2rem;
            }}
            h1 {{
                color: {DashboardVisualizer.COLORS['primary']};
                border-bottom: 2px solid {DashboardVisualizer.COLORS['primary']};
                padding-bottom: 10px;
            }}
            .stAlert {{
                border-radius: 10px;
            }}
            .metric-card {{
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 15px;
            }}
        </style>
        """, unsafe_allow_html=True)
        
        st.title("📊 Dashboard de Produtividade - Análise Detalhada")
        st.markdown("""
        *Visualização abrangente de métricas de desempenho e produtividade da equipe.*  
        Última atualização: {}
        """.format(datetime.now().strftime("%d/%m/%Y %H:%M")))
    
    @staticmethod
    def _formatar_mensagem_alerta(alerta: Dict[str, Any]) -> str:
        """Formata a mensagem de alerta para exibição consistente."""
        tipo_formatado = alerta['tipo'].replace('_', ' ').title()
        return f"**{tipo_formatado}** (Severidade: {alerta['severidade'].upper()}): {alerta['message']}"
    
    @staticmethod
    def mostrar_alertas(alertas: List[Dict[str, Any]]) -> None:
        """Exibe alertas categorizados por severidade com estilos visuais distintos.
        
        Args:
            alertas: Lista de dicionários contendo informações de alertas
        """
        if not alertas:
            st.success("✅ Nenhum alerta crítico identificado", icon="✅")
            return
            
        with st.expander("🚨 **Alertas do Sistema**", expanded=True):
            tabs = st.tabs(["Alta Severidade", "Média Severidade", "Baixa Severidade"])
            
            alertas_alta = [a for a in alertas if a['severidade'] == 'alta']
            alertas_media = [a for a in alertas if a['severidade'] == 'media']
            alertas_baixa = [a for a in alertas if a['severidade'] == 'baixa']
            
            with tabs[0]:
                if alertas_alta:
                    for alerta in alertas_alta:
                        st.error(DashboardVisualizer._formatar_mensagem_alerta(alerta), icon="⚠️")
                else:
                    st.info("Nenhum alerta de alta severidade", icon="ℹ️")
            
            with tabs[1]:
                if alertas_media:
                    for alerta in alertas_media:
                        st.warning(DashboardVisualizer._formatar_mensagem_alerta(alerta), icon="🔔")
                else:
                    st.info("Nenhum alerta de média severidade", icon="ℹ️")
            
            with tabs[2]:
                if alertas_baixa:
                    for alerta in alertas_baixa:
                        st.info(DashboardVisualizer._formatar_mensagem_alerta(alerta), icon="📌")
                else:
                    st.info("Nenhum alerta de baixa severidade", icon="ℹ️")
    
    @staticmethod
    def _processar_dados_consistencia(resumo: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Processa os dados para análise de consistência usando nomes padronizados."""
        colunas_necessarias = ['tecnico', 'semana', 'produtividade', 'meta_batida']
        faltantes = [col for col in colunas_necessarias if col not in resumo.columns]
        if faltantes:
            raise ValueError(f"DataFrame de resumo está faltando colunas: {faltantes}")
        consistencia = resumo.groupby('tecnico').agg(
            total_ciclos=('semana', 'count'),
            meta_batida=('meta_batida', 'sum'),
            media_produtividade=('produtividade', 'mean')
        ).reset_index()
        consistencia['percentual_metas_batidas'] = (
            consistencia['meta_batida'] / consistencia['total_ciclos'] * 100
        ).round(2)
        ranking = consistencia.sort_values('percentual_metas_batidas', ascending=False)
        return consistencia, ranking
    
    @staticmethod
    def mostrar_ranking_consistencia(resumo: pd.DataFrame, key_suffix: str = "") -> pd.DataFrame:
        """Exibe ranking de consistência com gráficos interativos."""
        st.subheader("🏆 Ranking de Consistência de Metas")
        st.markdown("""
        *Análise da frequência com que cada técnico atinge as metas estabelecidas.*  
        O percentual é calculado como (metas batidas / total de ciclos avaliados).
        """)

        with st.spinner("Processando dados de consistência..."):
            consistencia, ranking = DashboardVisualizer._processar_dados_consistencia(resumo)

            # Renomeia para exibição
            ranking_exibe = ranking.rename(columns={
                'percentual_metas_batidas': 'Percentual_Metas_Batidas',
                'media_produtividade': 'Media_Produtividade',
                'tecnico': 'Nome Colaborador'
            })

            col1, col2 = st.columns([1, 2])

            with col1:
                st.dataframe(
                    ranking_exibe.style
                    .background_gradient(subset=['Percentual_Metas_Batidas'], cmap='YlGnBu')
                    .format({'Percentual_Metas_Batidas': "{:.2f}%"}),
                    height=600
                )

            with col2:
                fig = px.bar(
                    ranking_exibe.head(15), 
                    x='Nome Colaborador', 
                    y='Percentual_Metas_Batidas', 
                    text='Percentual_Metas_Batidas',
                    title="🎯 Percentual de Metas Batidas por Técnico",
                    color='Media_Produtividade',
                    color_continuous_scale='Viridis',
                    labels={'Media_Produtividade': 'Média Produtividade'}
                )
                fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                fig.update_layout(
                    yaxis_title="% de Metas Batidas",
                    xaxis_title="Técnico",
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)

                # Gráfico de dispersão adicional
                fig2 = px.scatter(
                    ranking_exibe,
                    x='Media_Produtividade',
                    y='Percentual_Metas_Batidas',
                    trendline="ols",
                    title="📊 Relação entre Produtividade Média e % de Metas Batidas",
                    hover_name='Nome Colaborador',
                    labels={
                        'Media_Produtividade': 'Produtividade Média',
                        'Percentual_Metas_Batidas': '% Metas Batidas'
                    }
                )
                st.plotly_chart(fig2, use_container_width=True)

        return ranking
    
    @staticmethod
    def _calcular_streaks(dados: pd.DataFrame) -> Dict[str, Any]:
        """Calcula sequências de metas batidas/não batidas."""
        streak_info = {
            'maior_streak_positivo': 0,
            'maior_streak_negativo': 0,
            'current_pos': 0,
            'current_neg': 0
        }
        
        for meta in dados['meta_batida']:
            if meta == 1:
                streak_info['current_pos'] += 1
                streak_info['current_neg'] = 0
                streak_info['maior_streak_positivo'] = max(
                    streak_info['maior_streak_positivo'], 
                    streak_info['current_pos']
                )
            else:
                streak_info['current_neg'] += 1
                streak_info['current_pos'] = 0
                streak_info['maior_streak_negativo'] = max(
                    streak_info['maior_streak_negativo'], 
                    streak_info['current_neg']
                )
        
        return streak_info
    
    @staticmethod
    def mostrar_streaks(resumo: pd.DataFrame) -> None:
        """Exibe análise de sequências consecutivas de metas batidas ou não batidas."""
        st.subheader("📈 Análise de Sequências de Desempenho (Streaks)")
        st.markdown("""
        *Identifica os maiores períodos consecutivos onde técnicos bateram ou não bateram metas.*  
        """)
        
        streaks_data = []
        for tecnico in resumo['tecnico'].unique():
            dados = resumo[resumo['tecnico'] == tecnico].sort_values('semana')
            streak_info = DashboardVisualizer._calcular_streaks(dados)
            
            streaks_data.append({
                'Técnico': tecnico,
                'Maior Sequência Positiva': streak_info['maior_streak_positivo'],
                'Maior Sequência Negativa': streak_info['maior_streak_negativo'],
                'Total Semanas': len(dados)
            })
        
        df_streaks = pd.DataFrame(streaks_data).sort_values(
            by='Maior Sequência Positiva', 
            ascending=False
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top 10 Melhores Sequências**")
            st.dataframe(
                df_streaks.head(10).style
                .background_gradient(subset=['Maior Sequência Positiva'], cmap='YlGn')
                .set_properties(**{'text-align': 'center'}),
                height=400
            )
        
        with col2:
            st.markdown("**Top 10 Piores Sequências**")
            st.dataframe(
                df_streaks.sort_values('Maior Sequência Negativa', ascending=False)
                .head(10).style
                .background_gradient(subset=['Maior Sequência Negativa'], cmap='OrRd')
                .set_properties(**{'text-align': 'center'}),
                height=400
            )
        
        # Visualização adicional
        fig = px.bar(
            df_streaks.melt(id_vars=['Técnico'], 
                          value_vars=['Maior Sequência Positiva', 'Maior Sequência Negativa']),
            x='Técnico',
            y='value',
            color='variable',
            barmode='group',
            title='Comparação de Sequências Positivas e Negativas',
            labels={'value': 'Número de Semanas', 'variable': 'Tipo de Sequência'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def mostrar_padroes_desempenho(resumo: pd.DataFrame) -> None:
        """Exibe análise consolidada de padrões de desempenho."""
        st.subheader("📊 Análise de Padrões de Desempenho")
        st.markdown("""
        *Identificação de técnicos com padrões específicos de desempenho ao longo do tempo.*
        """)

        tabs = st.tabs(["📉 Em Queda", "🔄 Oscilantes", "📈 Em Crescimento", "🚫 Sem Bater Meta"])

        with tabs[0]:  # Técnicos em queda
            tecnicos_queda = []
            for tecnico in resumo['tecnico'].unique():
                dados = resumo[resumo['tecnico'] == tecnico].sort_values('semana')
                if len(dados) >= 4 and all(dados['meta_batida'].tail(3) == 0):
                    prod_diff = dados['produtividade'].iloc[-1] - dados['produtividade'].iloc[-4]
                    tecnicos_queda.append({
                        'Técnico': tecnico,
                        'Semanas em Queda': 3,
                        'Variação Produtividade': prod_diff
                    })

            if tecnicos_queda:
                df_queda = pd.DataFrame(tecnicos_queda).sort_values('Variação Produtividade')
                st.dataframe(
                    df_queda.style
                    .background_gradient(subset=['Variação Produtividade'], cmap='OrRd')
                    .format({'Variação Produtividade': "{:.1f}"}),
                    height=300
                )

                # Gráfico de exemplo para o primeiro técnico
                exemplo = df_queda.iloc[0]['Técnico']
                dados_exemplo = resumo[resumo['tecnico'] == exemplo].sort_values('semana')
                fig = px.line(
                    dados_exemplo,
                    x='semana',
                    y='produtividade',
                    title=f"Exemplo de Queda: {exemplo}",
                    markers=True
                )
                fig.add_hline(y=MetaConfig.SEMANAL, line_dash="dash", line_color="red")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("✅ Nenhum técnico em queda nas últimas 3 semanas.")

        with tabs[1]:  # Técnicos oscilantes
            oscilantes = []
            for tecnico in resumo['tecnico'].unique():
                dados = resumo[resumo['tecnico'] == tecnico].sort_values('semana')
                if len(dados) >= 4 and dados['meta_batida'].diff().abs().sum() > 2:
                    oscilantes.append({
                        'Técnico': tecnico,
                        'Mudanças': dados['meta_batida'].diff().abs().sum(),
                        'Produtividade Média': dados['produtividade'].mean()
                    })

            if oscilantes:
                df_oscilantes = pd.DataFrame(oscilantes).sort_values('Mudanças', ascending=False)
                st.dataframe(
                    df_oscilantes.style
                    .background_gradient(subset=['Mudanças'], cmap='YlOrRd')
                    .format({'Produtividade Média': "{:.1f}"}),
                    height=300
                )
            else:
                st.info("✅ Nenhum técnico oscilante identificado.")

        with tabs[2]:  # Técnicos em crescimento
            crescimento = []
            for tecnico in resumo['tecnico'].unique():
                dados = resumo[resumo['tecnico'] == tecnico].sort_values('semana')
                if len(dados) >= 3 and all(dados['meta_batida'].tail(3) == 1):
                    crescimento.append({
                        'Técnico': tecnico,
                        'Semanas Crescimento': 3,
                        'Ganho Produtividade': dados['produtividade'].iloc[-1] - dados['produtividade'].iloc[-4]
                    })

            if crescimento:
                df_crescimento = pd.DataFrame(crescimento).sort_values('Ganho Produtividade', ascending=False)
                st.dataframe(
                    df_crescimento.style
                    .background_gradient(subset=['Ganho Produtividade'], cmap='YlGn')
                    .format({'Ganho Produtividade': "{:.1f}"}),
                    height=300
                )
            else:
                st.info("ℹ️ Nenhum técnico em crescimento nas últimas 3 semanas.")

        with tabs[3]:  # Técnicos que nunca bateram meta
            nunca_bateram = resumo.groupby('tecnico')['meta_batida'].sum()
            nunca_bateram = nunca_bateram[nunca_bateram == 0].index.tolist()

            if nunca_bateram:
                df_nunca_bateram = pd.DataFrame({
                    'Técnico': nunca_bateram,
                    'Semanas Avaliadas': [len(resumo[resumo['tecnico'] == t]) for t in nunca_bateram],
                    'Produtividade Média': [resumo[resumo['tecnico'] == t]['produtividade'].mean()
                                           for t in nunca_bateram]
                })
                st.dataframe(
                    df_nunca_bateram.style
                    .background_gradient(subset=['Produtividade Média'], cmap='YlOrRd')
                    .format({'Produtividade Média': "{:.1f}"}),
                    height=300
                )
            else:
                st.success("🎉 Todos os técnicos bateram meta pelo menos uma vez!")
    
    @staticmethod
    def mostrar_evolucao_produtividade(resumo: pd.DataFrame, key_suffix: str = "") -> None:
        """Exibe gráfico de evolução temporal da produtividade."""
        st.subheader("📈 Evolução Temporal da Produtividade")
        st.markdown("""
        *Comparativo da produtividade por técnico ao longo do tempo.*  
        A linha vermelha tracejada representa a meta semanal estabelecida.
        """)
        
        try:
            prod = resumo.groupby(['Semana', 'Nome Colaborador'])['QTD. PROXXIMA | Produtivas - Fechamento Geral'].sum().reset_index()
            
            fig = px.line(
                prod, 
                x='Semana', 
                y='QTD. PROXXIMA | Produtivas - Fechamento Geral', 
                color='Nome Colaborador',
                line_shape='spline',
                title="Evolução da Produtividade por Técnico",
                labels={
                    'QTD. PROXXIMA | Produtivas - Fechamento Geral': 'Produtividade',
                    'Semana': 'Período'
                }
            )
            
            fig.add_hline(
                y=MetaConfig.SEMANAL, 
                line_dash="dash", 
                line_color="red",
                annotation_text="Meta Semanal", 
                annotation_position="bottom right"
            )
            
            fig.update_layout(
                hovermode='x unified',
                legend_title_text='Técnicos',
                xaxis_title='Semana',
                yaxis_title='Produtividade',
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True, key=f"grafico_evolucao_produtividade{key_suffix}")
            
            # Adicionando análise de variação
            st.markdown("### 📊 Análise de Variação")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Maiores Crescimentos**")
                ultimas_semanas = prod[prod['Semana'].isin(prod['Semana'].unique()[-2:])]
                pivot = ultimas_semanas.pivot(index='Nome Colaborador', columns='Semana', 
                                             values='QTD. PROXXIMA | Produtivas - Fechamento Geral')
                pivot['Variação'] = pivot.iloc[:, -1] - pivot.iloc[:, -2]
                st.dataframe(
                    pivot.sort_values('Variação', ascending=False).head(10)
                    .style.background_gradient(subset=['Variação'], cmap='YlGn')
                    .format("{:.1f}"),
                    height=300
                )
            
            with col2:
                st.markdown("**Maiores Quedas**")
                st.dataframe(
                    pivot.sort_values('Variação').head(10)
                    .style.background_gradient(subset=['Variação'], cmap='OrRd')
                    .format("{:.1f}"),
                    height=300
                )
                
        except Exception as e:
            st.error(f"⚠️ Erro ao gerar gráfico de evolução: {str(e)}")
    
    @staticmethod
    def mostrar_tendencia_tecnico(analise: Dict[str, Any]) -> None:
        """Exibe análise de tendência para um técnico específico."""
        if analise['status'] != 'ok':
            st.warning("⚠️ Dados insuficientes para análise de tendência")
            return
            
        st.subheader(f"📊 Análise de Tendência para {analise['tecnico']}")
        
        # Garantir que 'projecao_date' seja datetime.datetime nativo
        projecao_date = analise['projecao_date']
        
        # Converte para datetime.datetime puro
        if isinstance(projecao_date, pd.Timestamp):
            projecao_date = projecao_date.to_pydatetime()
        elif isinstance(projecao_date, np.datetime64):
            projecao_date = pd.to_datetime(projecao_date).to_pydatetime()
        elif not isinstance(projecao_date, datetime.datetime):
            raise TypeError(f"Tipo inesperado em 'projecao_date': {type(projecao_date)}")

    
        # Criando layout com métricas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="**Direção da Tendência**",
                value=analise['tendencia'].upper(),
                delta=f"Coeficiente: {analise['coeficiente']:.2f}",
                help="Positivo indica tendência de melhora, negativo indica queda"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="**Projeção Próxima Semana**",
                value=f"{analise['projecao']:.1f}",
                delta=f"{(analise['projecao'] - MetaConfig.SEMANAL):.1f} vs meta",
                help="Estimativa baseada na regressão linear dos últimos dados"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="**Confiança da Projeção**",
                value=f"{analise['confianca']:.0%}",
                help="R² da regressão linear, indica qualidade do ajuste"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Gráfico de tendência
        fig = go.Figure()
        
        # Dados históricos
        fig.add_trace(go.Scatter(
            x=analise['dados']['Semana'],
            y=analise['dados']['QTD. PROXXIMA | Produtivas - Fechamento Geral'],
            mode='lines+markers',
            name='Produtividade Real',
            line=dict(color=DashboardVisualizer.COLORS['primary'], width=3)
        ))
        
        # Linha de tendência
        fig.add_trace(go.Scatter(
            x=analise['tendencia_line']['x'],
            y=analise['tendencia_line']['y'],
            mode='lines',
            name='Linha de Tendência',
            line=dict(color=DashboardVisualizer.COLORS['danger'], width=2, dash='dash')
        ))
        
        # Meta
        fig.add_hline(
            y=MetaConfig.SEMANAL,
            line_dash="dot",
            line_color=DashboardVisualizer.COLORS['warning'],
            annotation_text="Meta Semanal",
            annotation_position="bottom right"
        )
        
       # Projeção (linha vertical)
        fig.add_vline(
            x=projecao_date,
            line_dash="dash",
            line_color=DashboardVisualizer.COLORS['success']
        )

# Anotação manual
        fig.add_annotation(
            x=projecao_date,
            y=analise['projecao'],
            text="Próxima Semana",
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40
        )
        
        fig.update_layout(
            title=f"Análise de Tendência - {analise['tecnico']}",
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recomendações baseadas na análise
        st.markdown("### 📌 Recomendações")
        if analise['tendencia'] == 'positiva':
            st.success(f"""
            **Oportunidade**: {analise['tecnico']} está em **crescimento consistente**.  
            🔹 Considere desafios adicionais ou mentoria para outros técnicos  
            🔹 Avalie possibilidade de reconhecimento pelo desempenho  
            🔹 Mantenha o monitoramento para sustentar a melhoria
            """)
        elif analise['tendencia'] == 'negativa':
            st.error(f"""
            **Atenção**: {analise['tecnico']} está em **queda de desempenho**.  
            🔹 Recomendado feedback individual imediato  
            🔹 Avaliar possíveis causas externas (equipamento, treinamento)  
            🔹 Considerar plano de ação com metas intermediárias
            """)
        else:
            st.info(f"""
            **Estabilidade**: {analise['tecnico']} mantém desempenho estável.  
            🔹 Identificar oportunidades de melhoria incremental  
            🔹 Avaliar se desempenho está adequado às expectativas  
            🔹 Manter acompanhamento regular
            """)