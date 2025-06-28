"""
Módulo para processamento e validação de dados.
"""

import pandas as pd
from typing import Tuple, Optional, Dict, Any, List  # Adicionei List aqui
from datetime import datetime
import streamlit as st
from src.config import COLUNAS_ORIGINAIS, COLUNAS_OBRIGATORIAS, MetaConfig

class DataProcessor:
    """Classe para processamento e validação de dados do dashboard."""

    def __init__(self, uploaded_file: Any, config: Dict[str, Any]):
        """
        Inicializa o processador de dados.
        
        Args:
            uploaded_file: Arquivo carregado via Streamlit
            config: Dicionário de configuração
        """
        self.uploaded_file = uploaded_file
        self.config = config
        self.df_principal: Optional[pd.DataFrame] = None

    def carregar_dados_principal(
        self, 
        aba_principal: str = '1. ANALÍTICO |  Produtivas -...'
    ) -> pd.DataFrame:
        """
        Carrega dados da aba principal do arquivo Excel.
        
        Args:
            aba_principal: Nome da aba principal
            
        Returns:
            DataFrame principal
            
        Raises:
            ValueError: Se o arquivo não puder ser lido
        """
        try:
            self.df_principal = pd.read_excel(self.uploaded_file, sheet_name=aba_principal)
            return self.df_principal
        except Exception as e:
            raise ValueError(f"Erro ao ler arquivo: {str(e)}")
    
    def validar_colunas(self, df: pd.DataFrame) -> bool:
        """
        Valida se as colunas obrigatórias estão presentes no DataFrame.

        Args:
            df: DataFrame a ser validado

        Returns:
            bool: True se todas as colunas obrigatórias estiverem presentes

        Raises:
            ValueError: Se colunas obrigatórias estiverem faltando
        """
        faltantes = [col for col in COLUNAS_OBRIGATORIAS if col not in df.columns]
        if faltantes:
            raise ValueError(f"Colunas obrigatórias faltando: {faltantes}")
        return True
    
    def validar_estrutura_arquivo(self):
        """Valida se o arquivo carregado possui a estrutura esperada."""
        if self.df_principal is None:
            raise ValueError("Dados principais não carregados")
        faltantes = [col for col in COLUNAS_OBRIGATORIAS if col not in self.df_principal.columns]
        if faltantes:
            raise ValueError(
                f"Colunas obrigatórias faltando no arquivo: {faltantes}\n"
                f"Colunas encontradas: {list(self.df_principal.columns)}"
            )

    def preprocessar_dados(self, feriados: List[datetime]) -> pd.DataFrame:
        """
        Pré-processa os dados principais, calculando semanas e metas.
        
        Args:
            feriados: Lista de feriados para cálculo de metas
            
        Returns:
            DataFrame pré-processado
            
        Raises:
            ValueError: Se os dados não puderem ser processados
        """
        if self.df_principal is None:
            raise ValueError("Dados principais não carregados")
            
        try:
            df = self.df_principal.copy()
            
            df = df.rename(columns={v: k for k, v in COLUNAS_ORIGINAIS.items()})

            # Mantém apenas as colunas necessárias
            df = df[list(COLUNAS_ORIGINAIS.keys())]
            # Processamento dos dados
            df['data_fechamento'] = pd.to_datetime(df['data_fechamento'], errors='coerce')
            df['semana'] = df['data_fechamento'] - pd.to_timedelta(df['data_fechamento'].dt.weekday, unit='D')
            
            # Calcular metas semanais
            metas = self.calcular_metas_semanais(df, feriados)
            
            # Criar resumo
            resumo = df.groupby(['tecnico', 'semana']).agg({
                'produtividade': 'sum',
                'protocolos': 'count'
            }).reset_index()
            
            resumo['meta_semana'] = resumo['semana'].map(metas)
            resumo['meta_batida'] = resumo['produtividade'] >= resumo['meta_semana']
            
            return resumo
        except Exception as e:
            raise ValueError(f"Erro no pré-processamento: {str(e)}")
    
    @staticmethod
    def calcular_meta(semana: datetime, feriados: List[datetime]) -> int:
        """
        Calcula a meta para uma semana específica considerando feriados.
        
        Args:
            semana: Data representando o início da semana
            feriados: Lista de feriados
            
        Returns:
            Meta ajustada para a semana
        """
        dias = pd.date_range(semana, semana + pd.Timedelta(days=6))
        qtd_feriados = sum(d in feriados for d in dias)
        return MetaConfig.SEMANAL - (qtd_feriados * MetaConfig.DIARIA)
    
    def calcular_metas_semanais(
        self, 
        df: pd.DataFrame, 
        feriados: List[datetime]
    ) -> Dict[datetime, int]:
        """
        Calcula metas para todas as semanas no DataFrame.
        
        Args:
            df: DataFrame com dados
            feriados: Lista de feriados
            
        Returns:
            Dicionário com metas por semana
        """
        return {
            semana: self.calcular_meta(semana, feriados) 
            for semana in df['semana'].dropna().unique()
        }

