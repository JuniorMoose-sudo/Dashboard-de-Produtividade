import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Produtividade - Dashboard", layout="wide")
st.title("📊 Dashboard de Produtividade")

uploaded_file = st.file_uploader("Faça upload da planilha (.xlsx)", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    col_tecnico = "Nome colaborador"
    col_pontuacao = "Produtivas-Fechamento Geral"
    col_data = next((col for col in df.columns if "data" in col.lower()), None)
    col_supervisor = next((col for col in df.columns if "supervisor" in col.lower()), None)

    if not col_data or not col_supervisor:
        st.error("❌ Colunas obrigatórias não encontradas (data ou supervisor).")
        st.stop()

    # Limpeza
    df = df[[col_tecnico, col_data, col_pontuacao, col_supervisor]].dropna()
    df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
    df = df.dropna(subset=[col_data])

    # Agrupamento por técnico, data e supervisor
    df = df.groupby([col_tecnico, col_data, col_supervisor], as_index=False)[col_pontuacao].sum()

    df['Data'] = pd.to_datetime(df[col_data]).dt.date
    df['Dia'] = pd.to_datetime(df[col_data]).dt.day
    df['Semana_Mes'] = ((pd.to_datetime(df[col_data]) - pd.to_datetime(df[col_data]).min()).dt.days // 7) + 1
    df['Dia da Semana'] = pd.to_datetime(df[col_data]).dt.day_name()

    # Criar coluna com o início e fim da semana (segunda a domingo)
    df['Data'] = pd.to_datetime(df['Data'])
    df['Inicio_Semana'] = df['Data'] - pd.to_timedelta(df['Data'].dt.weekday, unit='d')
    df['Fim_Semana'] = df['Inicio_Semana'] + pd.Timedelta(days=6)
    df['Periodo_Semana'] = df['Inicio_Semana'].dt.strftime('%d/%m') + " a " + df['Fim_Semana'].dt.strftime('%d/%m')
    df['Semana'] = df['Inicio_Semana'].dt.strftime('%Y-%m-%d')

    # -------------------- FILTROS --------------------
    st.sidebar.header("🔎 Filtros")
    supervisores_disponiveis = df[col_supervisor].dropna().unique().tolist()
    supervisores_selecionados = st.sidebar.multiselect("Filtrar por supervisor:", options=supervisores_disponiveis, default=supervisores_disponiveis)
    df = df[df[col_supervisor].isin(supervisores_selecionados)]

    tecnicos_disponiveis = df[col_tecnico].unique().tolist()
    tecnicos_selecionados = st.sidebar.multiselect("Filtrar por técnico:", options=tecnicos_disponiveis, default=tecnicos_disponiveis)
    df = df[df[col_tecnico].isin(tecnicos_selecionados)]

    semanas_disponiveis = sorted(df['Periodo_Semana'].unique())
    semanas_selecionadas = st.sidebar.multiselect("Filtrar por semana:", options=semanas_disponiveis, default=semanas_disponiveis)
    df = df[df['Periodo_Semana'].isin(semanas_selecionadas)]

    qtd_equipes = st.sidebar.number_input("Quantidade de equipes (manual):", min_value=1, value=len(tecnicos_selecionados), step=1)

    # -------------------- TABELA PIVOTADA DIÁRIA --------------------
    tabela_dia = df.pivot_table(index=col_tecnico, columns='Dia', values=col_pontuacao, aggfunc='sum', fill_value=0)
    tabela_dia.columns = [f'Dia {col}' for col in tabela_dia.columns]
    tabela_dia['Total Parcial'] = tabela_dia.sum(axis=1)

    st.subheader("📅 Pontuação Diária por Técnico")
    st.dataframe(tabela_dia, use_container_width=True)

    # -------------------- META DIÁRIA --------------------
    pontuacao_por_dia = df.groupby('Data')[col_pontuacao].sum().reset_index()
    pontuacao_por_dia['Dia da Semana'] = pd.to_datetime(pontuacao_por_dia['Data']).dt.day_name()
    pontuacao_por_dia['Meta Diária'] = pontuacao_por_dia['Dia da Semana'].apply(
        lambda d: 0 if d in ['Saturday', 'Sunday'] else 8 * qtd_equipes
    )
    pontuacao_por_dia['% Meta Atingida'] = (pontuacao_por_dia[col_pontuacao] / pontuacao_por_dia['Meta Diária'] * 100).fillna(0).round(1)

    st.subheader("🎯 Meta Diária vs Realizado")
    st.dataframe(pontuacao_por_dia, use_container_width=True)

    fig_meta = px.bar(pontuacao_por_dia, x='Data', y=[col_pontuacao, 'Meta Diária'],
                      barmode='group', title="📊 Realizado vs Meta Diária")
    st.plotly_chart(fig_meta, use_container_width=True)

    # -------------------- META PARCIAL VS IDEAL --------------------
    dias_uteis = pontuacao_por_dia[pontuacao_por_dia['Meta Diária'] > 0].shape[0]
    meta_total_ideal = dias_uteis * 8 * qtd_equipes
    pontuacao_total_parcial = df[col_pontuacao].sum()

    st.subheader("📈 Pontuação Total Parcial vs Meta Ideal")
    col1, col2 = st.columns(2)
    col1.metric("🔵 Pontuação Parcial Total", f"{pontuacao_total_parcial:.0f}")
    col2.metric("🟢 Meta Total Ideal", f"{meta_total_ideal:.0f}")

    fig_total = px.bar(x=["Pontuação Total", "Meta Ideal"],
                       y=[pontuacao_total_parcial, meta_total_ideal],
                       color=["Pontuação", "Meta"],
                       title="📊 Atingimento Total do Mês")
    st.plotly_chart(fig_total, use_container_width=True)

    # -------------------- RANKING --------------------
    ranking = tabela_dia['Total Parcial'].sort_values(ascending=False).reset_index()
    ranking.columns = [col_tecnico, "Pontuação Total Parcial"]
    st.subheader("🏆 Top 10 Técnicos por Pontuação Total Parcial")
    st.dataframe(ranking.head(10))

    fig_rank = px.bar(ranking.head(10), x="Pontuação Total Parcial", y=col_tecnico,
                      orientation='h', title="🥇 Top 10 Técnicos", color="Pontuação Total Parcial")
    st.plotly_chart(fig_rank, use_container_width=True)

    # -------------------- HORAS EXTRAS --------------------
    st.sidebar.markdown("### ⏱️ Horas Extras por Técnico")
    horas_extras_dict = {
        tecnico: st.sidebar.number_input(f"Horas extras - {tecnico}:", min_value=0.0, value=0.0, step=0.5, key=f"he_{tecnico}")
        for tecnico in tecnicos_selecionados
    }

    ranking['Horas Extras'] = ranking[col_tecnico].map(horas_extras_dict)
    ranking['Produtividade por Hora Extra'] = ranking.apply(
        lambda row: row["Pontuação Total Parcial"] / row["Horas Extras"] if row["Horas Extras"] > 0 else 0,
        axis=1
    )

    st.subheader("⚙️ Produtividade por Hora Extra")
    st.dataframe(ranking[[col_tecnico, "Pontuação Total Parcial", "Horas Extras", "Produtividade por Hora Extra"]])

    fig_he = px.bar(
        ranking.sort_values("Produtividade por Hora Extra", ascending=False),
        x="Produtividade por Hora Extra", y=col_tecnico,
        orientation='h', title="📈 Produtividade por Hora Extra (Top Técnicos)",
        color="Produtividade por Hora Extra"
    )
    st.plotly_chart(fig_he, use_container_width=True)

    # -------------------- CONTRIBUIÇÃO TOP 20% --------------------
    ranking_sorted = ranking.sort_values("Horas Extras", ascending=False).reset_index(drop=True)
    top_n = max(1, int(len(ranking_sorted) * 0.20))
    top_he = ranking_sorted.head(top_n)

    pontuacao_top_he = top_he["Pontuação Total Parcial"].sum()
    pontuacao_total_geral = ranking["Pontuação Total Parcial"].sum()
    contribuicao_pct = (pontuacao_top_he / pontuacao_total_geral) * 100 if pontuacao_total_geral > 0 else 0

    st.subheader("📊 Contribuição dos Técnicos com Mais Horas Extras")
    st.markdown(f"""
- Técnicos no top 20% de horas extras: **{top_n}**
- Pontuação total deles: **{pontuacao_top_he:.0f}**
- Contribuição para o total: **{contribuicao_pct:.1f}%**
""")

    # -------------------- GRÁFICO SEMANAL --------------------
    st.subheader("📅 Desempenho Semanal por Técnico")
    semanal = df.groupby([col_tecnico, 'Periodo_Semana'])[col_pontuacao].sum().reset_index()
    fig_semanal = px.bar(semanal, x='Periodo_Semana', y=col_pontuacao, color=col_tecnico,
                         title="📈 Pontuação Semanal por Técnico", barmode="group")
    st.plotly_chart(fig_semanal, use_container_width=True)

else:
    st.info("Por favor, envie a planilha para iniciar.")
