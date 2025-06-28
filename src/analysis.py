"""
Módulo com análises avançadas de produtividade.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any  # Adicionei Any aqui
import numpy as np
from src.config import MetaConfig
from datetime import datetime, timedelta

class PerformanceAnalyzer:
    """Classe para análises avançadas de performance."""
    
    def __init__(self, df_principal: pd.DataFrame, df_bairros: pd.DataFrame, config: Dict[str, Any]):
        """
        Inicializa o analisador de performance.
        
        Args:
            df_principal: DataFrame com dados principais
            df_bairros: DataFrame com dados de bairros
            config: Configurações do sistema
        """
        self.df = df_principal
        self.df_bairros = df_bairros
        self.config = config
        
        # Renomear colunas para padronização
        self.df = self.df.rename(columns={
            'tecnico': 'Nome Colaborador',
            'semana': 'Semana',
            'meta_batida': 'Meta Batida',
            'produtividade': 'QTD. PROXXIMA | Produtivas - Fechamento Geral'  # ajuste aqui conforme o nome real
        })
    
    def identificar_tendencia(
        self, 
        tecnico: str, 
        periodo_semanas: int = 4
    ) -> Dict[str, Any]:
        """
        Identifica tendência de performance para um técnico.
        """
        dados = self.df[self.df['Nome Colaborador'] == tecnico].sort_values('Semana')
        if len(dados) < periodo_semanas:
            return {'status': 'insuficiente', 'message': 'Dados insuficientes'}

        recente = dados.tail(periodo_semanas)
        x = np.arange(len(recente))
        y = recente['QTD. PROXXIMA | Produtivas - Fechamento Geral'].values
        coef = np.polyfit(x, y, 1)

        # Calcule a data de projeção (próxima semana)
        if not dados.empty and 'Semana' in dados.columns:
            ultima_semana = dados['Semana'].iloc[-1]
            if isinstance(ultima_semana, str):
                ultima_semana = pd.to_datetime(ultima_semana)
            projecao_date = ultima_semana + timedelta(weeks=1)
        else:
            projecao_date = None

        # Monta o eixo X da linha de tendência com datas
        tendencia_x = list(recente['Semana'])
        tendencia_x = [pd.to_datetime(x) for x in tendencia_x]
        if projecao_date is not None:
            projecao_date = pd.to_datetime(projecao_date)
            tendencia_x.append(projecao_date)

        # O eixo Y deve ser calculado com base no índice sequencial dos pontos
        tendencia_y = [coef[0] * i + coef[1] for i in range(len(tendencia_x))]

        return {
            'status': 'ok',
            'tecnico': tecnico,
            'tendencia': 'alta' if coef[0] > 0.5 else 'baixa' if coef[0] < -0.5 else 'estavel',
            'coeficiente': float(coef[0]),
            'projecao': float(coef[0] * periodo_semanas + coef[1]),
            'confianca': 1.0,
            'dados': recente.reset_index(drop=True),
            'ultima_meta': float(dados['Meta Batida'].iloc[-1]) if not dados.empty else None,
            'tendencia_line': {
                'x': tendencia_x,
                'y': tendencia_y
            },
            'projecao_date': projecao_date
        }
    
    def analisar_impacto_bairro(self, tecnico: str) -> Dict[str, Any]:
        """
        Analisa o impacto do bairro na performance do técnico.
        
        Args:
            tecnico: Nome do técnico
            
        Returns:
            Dicionário com análise de impacto por bairro
        """
        if 'Bairro' not in self.df.columns:
            return {'status': 'error', 'message': 'Dados de bairro não disponíveis'}
        
        dados = self.df[self.df['Nome Colaborador'] == tecnico]
        if dados.empty:
            return {'status': 'error', 'message': 'Técnico não encontrado'}
        
        por_bairro = dados.groupby('Bairro').agg({
            'Pontuação': ['mean', 'count'],
            'Meta Batida': 'mean'
        }).reset_index()
        
        por_bairro.columns = ['Bairro', 'Pontuação Média', 'Atendimentos', 'Taxa Sucesso']
        por_bairro = por_bairro.sort_values('Pontuação Média', ascending=False)
        
        return {
            'status': 'ok',
            'melhor_bairro': por_bairro.iloc[0].to_dict(),
            'pior_bairro': por_bairro.iloc[-1].to_dict(),
            'variabilidade': float(por_bairro['Pontuação Média'].std())
        }
    
    def prever_meta_proxima_semana(
        self, 
        tecnico: str, 
        modelo: str = 'media_movel'
    ) -> Dict[str, Any]:
        """
        Prevê performance para a próxima semana.
        
        Args:
            tecnico: Nome do técnico
            modelo: Modelo de previsão ('media_movel' ou 'regressao')
            
        Returns:
            Dicionário com previsão e métricas
        """
        dados = self.df[self.df['Nome Colaborador'] == tecnico].sort_values('Semana')
        if len(dados) < 3:
            return {'status': 'insuficiente', 'message': 'Dados insuficientes'}
        
        if modelo == 'media_movel':
            previsao = dados['Pontuação'].rolling(3).mean().iloc[-1]
        else:  # regressao
            x = np.arange(len(dados))
            y = dados['Pontuação'].values
            coef = np.polyfit(x, y, 1)
            previsao = coef[0] * (len(dados) + 1) + coef[1]
        
        ultima_meta = dados['Meta Semana'].iloc[-1]
        return {
            'status': 'ok',
            'previsao': float(previsao),
            'ultima_meta': float(ultima_meta),
            'diferenca': float(previsao - ultima_meta),
            'modelo': modelo
        }
    
    def gerar_alertas(self) -> List[Dict[str, Any]]:
        """
        Gera alertas baseados em anomalias e padrões nos dados.
        
        Returns:
            Lista de alertas identificados
        """
        alertas = []
        
        # Alertas para técnicos com queda de performance
        for tecnico in self.df['Nome Colaborador'].unique():
            dados = self.df[self.df['Nome Colaborador'] == tecnico].sort_values('Semana')
            if len(dados) >= 3:
                ultimos = dados.tail(3)
                if (ultimos['Meta Batida'].iloc[0] and 
                    not ultimos['Meta Batida'].iloc[1] and 
                    not ultimos['Meta Batida'].iloc[2]):
                    alertas.append({
                        'tipo': 'queda_performance',
                        'tecnico': tecnico,
                        'severidade': 'alta',
                        'message': f'{tecnico} teve queda nas últimas 3 semanas'
                    })
        
        # Alertas para bairros problemáticos
        if 'Bairro' in self.df.columns:
            bairros_problematicos = self.df.groupby('Bairro')['Meta Batida'].mean()
            bairros_problematicos = bairros_problematicos[bairros_problematicos < 0.3]
            for bairro in bairros_problematicos.index:
                alertas.append({
                    'tipo': 'bairro_problematico',
                    'bairro': bairro,
                    'severidade': 'media',
                    'message': f'Bairro {bairro} com baixa taxa de sucesso'
                })
        
        return alertas

    def plotar_tendencia(self, tecnico: str):
        """
        Plota a tendência de performance de um técnico.
        
        Args:
            tecnico: Nome do técnico
        """
        analise = self.identificar_tendencia(tecnico)

        if analise['status'] != 'ok':
            print(analise['message'])
            return

        import plotly.graph_objects as go

        fig = go.Figure()

        # Garantir que todas as datas sejam datetime.datetime (não Timestamp)
        semanas_real = [
            dt.to_pydatetime() if isinstance(dt, pd.Timestamp) else dt
            for dt in analise['dados']['Semana']
        ]
        fig.add_trace(go.Scatter(
            x=semanas_real,
            y=analise['dados']['QTD. PROXXIMA | Produtivas - Fechamento Geral'],
            mode='lines+markers',
            name='Dados Reais'
        ))

        # Linha de tendência
        tendencia_x = [
            dt.to_pydatetime() if isinstance(dt, pd.Timestamp) else dt
            for dt in analise['tendencia_line']['x']
        ]
        fig.add_trace(go.Scatter(
            x=tendencia_x,
            y=analise['tendencia_line']['y'],
            mode='lines',
            name='Tendência',
            line=dict(color='red')
        ))

        # Projeção
        projecao_date = analise['projecao_date']
        if isinstance(projecao_date, pd.Timestamp):
            projecao_date = projecao_date.to_pydatetime()

        if projecao_date:
            fig.add_trace(go.Scatter(
                x=[projecao_date],
                y=[analise['projecao']],
                mode='markers',
                name='Projeção',
                marker=dict(color='green', size=10)
            ))
            fig.add_vline(x=projecao_date, line_dash="dot", line_color="orange")

        fig.update_layout(
            title=f'Tendência de Performance - {tecnico}',
            xaxis_title='Semana',
            yaxis_title='Produtividade',
            legend_title='Legenda',
            template='plotly_white'
        )

        fig.show()

