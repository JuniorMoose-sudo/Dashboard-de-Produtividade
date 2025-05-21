# 📊 Dashboard de Produtividade com Streamlit

Este projeto é um **dashboard interativo** construído com [Streamlit](https://streamlit.io/) para acompanhar a **produtividade de equipes** a partir de uma planilha Excel (.xlsx). Ele oferece visualizações ricas, filtros dinâmicos e análise de metas, permitindo uma gestão eficiente da performance diária e semanal dos técnicos.

---

## 🚀 Funcionalidades

- 📅 Visualização da **pontuação diária por técnico**
- 🎯 Comparativo entre **pontuação real e meta diária**
- 📈 Gráficos de **meta total parcial vs ideal**
- 🏆 Ranking dos **Top 10 técnicos**
- ⏱️ Cálculo de **produtividade por hora extra**
- 📊 Contribuição dos técnicos com mais horas extras
- 📆 Análise **semanal de desempenho**
- 🔎 Filtros interativos por **supervisor**, **técnico** e **semana**

---

## 📂 Estrutura esperada da planilha

A planilha enviada precisa conter as seguintes colunas:

- **Nome colaborador** (nome do técnico)
- **Supervisor** (responsável direto)
- **Data** (data do serviço)
- **Produtivas-Fechamento Geral** (pontuação diária)

> As colunas de **data** e **supervisor** devem conter essas palavras-chave para serem detectadas automaticamente.

---

## ✅ Requisitos

- Python 3.8 ou superior
- Pacotes:

```bash
pip install streamlit pandas plotly openpyxl

📈 Exemplo de uso
Envie uma planilha .xlsx

Acompanhe as pontuações por técnico

Ajuste manualmente a quantidade de equipes e horas extras por técnico

Visualize os rankings e atingimento das metas

🧠 Sobre
Este projeto foi desenvolvido para facilitar o acompanhamento da produtividade de técnicos em campo, com foco em simplicidade, insights visuais e gestão baseada em dados.


