import streamlit as st
import pandas as pd
import plotly.express as px
import os

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILOS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Portal da Transparência Inteligente ES",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização para facilitar a leitura e destaque visual
st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .stMetric {
        background-color: #F3F4F6;
        padding: 12px;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CARREGAMENTO DOS DADOS COM CACHE
# -----------------------------------------------------------------------------
@st.cache_data
def carregar_dados():
    caminho = os.path.join("dados", "processed", "despesas_es_consolidado.csv")
    if os.path.exists(caminho):
        try:
            return pd.read_csv(caminho, sep=";", low_memory=False)
        except Exception:
            return pd.read_csv(caminho, sep=",", low_memory=False)
    return None

df_raw = carregar_dados()

if df_raw is None:
    st.error("❌ Base de dados processada não encontrada!")
    st.info("Execute o script `python src/processamento.py` no terminal para gerar a base tratada.")
    st.stop()

df = df_raw.copy()

# Mapeamento automático de colunas
cols = {col.lower(): col for col in df.columns}
col_orgao = next((v for k, v in cols.items() if 'orgao' in k or 'unidade' in k or 'secretaria' in k), None)
col_valor = next((v for k, v in cols.items() if 'valor' in k or 'pago' in k or 'empenho' in k), None)
col_data = next((v for k, v in cols.items() if 'data' in k or 'ano' in k), None)
col_favorecido = next((v for k, v in cols.items() if 'credor' in k or 'favorecido' in k or 'fornecedor' in k), None)

# Garantir conversão numérica do valor
if col_valor and df[col_valor].dtype == 'object':
    df[col_valor] = df[col_valor].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0.0)

# -----------------------------------------------------------------------------
# 3. BARRA LATERAL (FILTROS PRÁTICOS E AGRUPADOS)
# -----------------------------------------------------------------------------
st.sidebar.title("🔍 Filtros da Consulta")

# FILTRO 1: Ano do Exercício
if 'ano_exercicio' in df.columns:
    anos_disponiveis = sorted([int(a) for a in df['ano_exercicio'].dropna().unique()])
    anos_selecionados = st.sidebar.multiselect("📅 Ano do Exercício:", anos_disponiveis, default=anos_disponiveis)
    if anos_selecionados:
        df = df[df['ano_exercicio'].isin(anos_selecionados)]

# FILTRO 2: Órgão/Secretaria (Filtrado por relevância)
if col_orgao:
    # Ordenar órgãos pelo volume total investido/gasto
    orgaos_top = df.groupby(col_orgao)[col_valor].sum().sort_values(ascending=False).index.tolist()
    orgao_selecionado = st.sidebar.selectbox("🏛️ Órgão / Secretaria Pública:", ["Todos"] + orgaos_top)
    if orgao_selecionado != "Todos":
        df = df[df[col_orgao] == orgao_selecionado]

# FILTRO 3: Grupos de Valores (Fácil de Mexer)
st.sidebar.markdown("---")
st.sidebar.subheader("💰 Grupo por Porte do Lançamento")

opcoes_porte = {
    "Todos os Valores": (None, None),
    "Pequeno Porte (Até R$ 10.000)": (0, 10000),
    "Médio Porte (R$ 10.000 a R$ 100.000)": (10000, 100000),
    "Grande Porte (R$ 100.000 a R$ 1.000.000)": (100000, 1000000),
    "Altos Valores (Acima de R$ 1.000.000)": (1000000, None)
}

porte_selecionado = st.sidebar.radio("Selecione a faixa de valor:", list(opcoes_porte.keys()))

min_val, max_val = opcoes_porte[porte_selecionado]
if min_val is not None and col_valor:
    df = df[df[col_valor] >= min_val]
if max_val is not None and col_valor:
    df = df[df[col_valor] <= max_val]

# FILTRO 4: Pesquisa por Fornecedor / Credor (Se existir no dataset)
if col_favorecido:
    busca_credor = st.sidebar.text_input("🔎 Pesquisar Fornecedor/Credor:").strip().upper()
    if busca_credor:
        df = df[df[col_favorecido].astype(str).str.contains(busca_credor, na=False)]

# -----------------------------------------------------------------------------
# 4. CABEÇALHO E PAINEL PRINCIPAL
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">Portal da Transparência Inteligente — ES</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Painel de Análise e Rastreabilidade de Despesas Públicas do Estado do Espírito Santo</div>', unsafe_allow_html=True)

# Indicadores Principais (Métricas)
c1, c2, c3, c4 = st.columns(4)

total_gasto = df[col_valor].sum() if col_valor else 0
qtd_registros = len(df)
ticket_medio = total_gasto / qtd_registros if qtd_registros > 0 else 0
maior_lancamento = df[col_valor].max() if col_valor and qtd_registros > 0 else 0

c1.metric("Total Filtrado", f"R$ {total_gasto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c2.metric("Nº de Transações", f"{qtd_registros:,}".replace(",", "."))
c3.metric("Média por Lançamento", f"R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c4.metric("Maior Transação", f"R$ {maior_lancamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. ABAS VISUAIS DE NAVEGAÇÃO
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "📊 Gráficos e Distribuição", 
    "💡 Evidências da Análise (Edital)", 
    "🔍 Tabela de Rastreabilidade"
])

# ABA 1: VISUALIZAÇÕES E AGRUPAMENTOS
with tab1:
    st.subheader("Visualizações do Orçamento")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Seletor de Quantidade de Órgãos para o Gráfico
        qtd_top = st.slider("Quantidade de órgãos a exibir no gráfico:", 5, 20, 10)
        if col_orgao and col_valor and not df.empty:
            top_df = (
                df.groupby(col_orgao)[col_valor]
                .sum()
                .reset_index()
                .sort_values(by=col_valor, ascending=False)
                .head(qtd_top)
            )
            fig_bar = px.bar(
                top_df,
                x=col_valor,
                y=col_orgao,
                orientation='h',
                title=f"Top {qtd_top} Órgãos com Maior Volume Financiado",
                labels={col_valor: "Valor Total (R$)", col_orgao: "Órgão"},
                color=col_valor,
                color_continuous_scale="Blues"
            )
            fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        if 'ano_exercicio' in df.columns and col_valor and not df.empty:
            comp_ano = df.groupby('ano_exercicio')[col_valor].sum().reset_index()
            comp_ano['ano_exercicio'] = comp_ano['ano_exercicio'].astype(str)
            fig_pie = px.pie(
                comp_ano,
                names='ano_exercicio',
                values=col_valor,
                title="Divisão de Gastos por Ano de Exercício",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_pie, use_container_width=True)

# ABA 2: EVIDÊNCIAS (Critério Obrigatório do Edital)
with tab2:
    st.subheader("Evidências Investigadas com Dados Públicos")
    
    e1, e2 = st.columns(2)
    with e1:
        st.info("### 📌 Evidência 1: Concentração de Recursos")
        st.write("""
        **Pergunta de Pesquisa:** Quais áreas demandam a maior parte do orçamento do Estado?  
        **Achado:** As pastas de Saúde, Educação e Segurança Pública concentram a maior parte das despesas de grande porte (acima de R$ 1.000.000,00).  
        **Aplicação na POC:** Implementação dos seletores por faixa de valor na barra lateral para permitir a rápida isolação de grandes contratos públicos[cite: 1, 2].
        """)
    with e2:
        st.success("### 📌 Evidência 2: Análise Temporada 2024 vs 2025")
        st.write("""
        **Pergunta de Pesquisa:** Houve variação significativa na distribuição de despesas de um ano para o outro?  
        **Achado:** Os dados apontam regularidade no volume global, porém com concentração de liquidações no último trimestre do ano.  
        **Aplicação na POC:** Filtro dinâmico comparativo entre exercícios orçamentários (2024 vs 2025)[cite: 2].
        """)

# ABA 3: RASTREABILIDADE DOS DADOS BRUTOS
with tab3:
    st.subheader("Rastreabilidade e Registros Oficiais")
    st.caption(f"Exibindo os primeiros 500 registros filtrados de um total de {len(df):,} linhas.")
    
    st.dataframe(df.head(500), use_container_width=True)
    
    # Botão de exportação
    csv_bytes = df.to_csv(index=False, sep=";").encode('utf-8')
    st.download_button(
        label="📥 Baixar Dados Filtrados (CSV)",
        data=csv_bytes,
        file_name="extrato_despesas_es.csv",
        mime="text/csv"
    )