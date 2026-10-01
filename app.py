import os
import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILOS VISUAIS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Portal da Transparência Inteligente | ES",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .header-box {
        background: linear-gradient(90deg, #1E3A8A 0%, #1E40AF 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .header-title {
        font-size: 2.1rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .header-subtitle {
        font-size: 1.0rem;
        opacity: 0.9;
        font-weight: 400;
    }
    
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.55rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: #94A3B8;
        margin-top: 2px;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        border-radius: 8px 8px 0px 0px;
        font-weight: 600;
        padding: 10px 18px;
    }
    </style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. CARREGAMENTO DOS DADOS COM CACHE
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="A carregar base de despesas públicas...")
def carregar_dados_consolidados():
    caminho = os.path.join("dados", "processed", "despesas_es_consolidado.csv")
    if not os.path.exists(caminho):
        return None
    return pd.read_csv(caminho, sep=";", low_memory=False)

df_raw = carregar_dados_consolidados()

if df_raw is None:
    st.error("❌ Base consolidada de despesas não encontrada!")
    st.info("Execute `python src/processamento.py` no terminal para gerar a base tratada.")
    st.stop()

df = df_raw.copy()

# -----------------------------------------------------------------------------
# 3. FILTROS DINÂMICOS (SIDEBAR)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bank-building.png", width=64)
    st.title("Filtros do Painel")
    st.caption("Origem: Dados Abertos - Governo do Estado do ES (2024–2025)")
    st.markdown("---")

    tipo_metrica = st.selectbox(
        "📌 Métrica Financeira:",
        options=["valorpago", "valorliquidado", "valorempenho"],
        format_func=lambda x: {
            "valorpago": "Valor Pago (Efetivado)",
            "valorliquidado": "Valor Liquidado (Nota Atestada)",
            "valorempenho": "Valor Empenhado (Reservado)"
        }[x]
    )

    with st.expander("📅 Período & Exercício", expanded=True):
        if 'ano_exercicio' in df.columns:
            anos_unicos = sorted(df['ano_exercicio'].dropna().unique().astype(int))
            anos_sel = st.multiselect("Ano de Referência:", anos_unicos, default=anos_unicos)
            if anos_sel:
                df = df[df['ano_exercicio'].isin(anos_sel)]

    with st.expander("🏛️️ Órgãos e Secretarias", expanded=True):
        if 'orgao' in df.columns and not df.empty:
            top_orgaos = (
                df.groupby('orgao')[tipo_metrica]
                .sum()
                .sort_values(ascending=False)
                .index.tolist()
            )
            orgao_sel = st.selectbox("Órgão / Secretaria Pública:", ["Todos"] + top_orgaos)
            if orgao_sel != "Todos":
                df = df[df['orgao'] == orgao_sel]

    with st.expander("💰 Faixas de Impacto Financeiro", expanded=False):
        opcoes_porte = {
            "Todos os Valores": (None, None),
            "Micro despesas (Até R$ 10.000)": (0, 10000),
            "Médio porte (R$ 10.000 a R$ 100.000)": (10000, 100000),
            "Grande porte (R$ 100.000 a R$ 1.000.000)": (100000, 1000000),
            "Grandes Contratos (Acima de R$ 1.000.000)": (1000000, None)
        }
        porte_sel = st.radio("Selecione a faixa:", list(opcoes_porte.keys()))
        min_v, max_v = opcoes_porte[porte_sel]

        if min_v is not None:
            df = df[df[tipo_metrica] >= min_v]
        if max_v is not None:
            df = df[df[tipo_metrica] <= max_v]

    with st.expander("🔎 Fornecedor & Licitação", expanded=False):
        if 'tipolicitacao' in df.columns:
            tipos_licitacao = ["Todos"] + sorted([t for t in df['tipolicitacao'].dropna().unique() if t != "NÃO INFORMADO"])
            licitacao_sel = st.selectbox("Tipo de Licitação:", tipos_licitacao)
            if licitacao_sel != "Todos":
                df = df[df['tipolicitacao'] == licitacao_sel]

        busca_fornecedor = st.text_input("Buscar Fornecedor ou CNPJ:").strip().upper()
        if busca_fornecedor:
            filtro_favorecido = df['favorecido'].astype(str).str.contains(busca_fornecedor, na=False)
            filtro_doc = df['cpfcnpjnis'].astype(str).str.contains(busca_fornecedor, na=False) if 'cpfcnpjnis' in df.columns else False
            df = df[filtro_favorecido | filtro_doc]

    st.markdown("---")
    st.info(f"📊 **{len(df):,}** registos encontrados.")

# -----------------------------------------------------------------------------
# 4. CABEÇALHO E INDICADORES DE TOPO (KPIs)
# -----------------------------------------------------------------------------
st.markdown("""
    <div class="header-box">
        <div class="header-title">Portal da Transparência Inteligente — Espírito Santo</div>
        <div class="header-subtitle">
            Plataforma de auditoria orçamental, análise cívica e rastreabilidade de despesas públicas estaduais.
        </div>
    </div>
""", unsafe_allow_html=True)

total_volume = df[tipo_metrica].sum() if not df.empty else 0.0
total_linhas = len(df)
media_transacao = total_volume / total_linhas if total_linhas > 0 else 0.0
maior_valor = df[tipo_metrica].max() if total_linhas > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Volume Total</div>
            <div class="metric-value">R$ {total_volume:,.2f}</div>
            <div class="metric-sub">Soma do recorte filtrado</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Lançamentos</div>
            <div class="metric-value">{total_linhas:,}</div>
            <div class="metric-sub">Atos contabilísticos processados</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Ticket Médio</div>
            <div class="metric-value">R$ {media_transacao:,.2f}</div>
            <div class="metric-sub">Média por lançamento</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Maior Operação</div>
            <div class="metric-value">R$ {maior_valor:,.2f}</div>
            <div class="metric-sub">Pico individual identificado</div>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# -----------------------------------------------------------------------------
# 5. ABAS PRINCIPAIS DE NAVEGAÇÃO
# -----------------------------------------------------------------------------
tab_macro, tab_auditoria, tab_dados = st.tabs([
    "📊 Panorama Executivo",
    "⚖️ Auditoria & Contratações",
    "🔍 Rastreabilidade & Microdados"
])

# -----------------------------------------------------------------------------
# ABA 1: PANORAMA EXECUTIVO
# -----------------------------------------------------------------------------
with tab_macro:
    if df.empty:
        st.warning("⚠️ Nenhum registo coincide com os filtros selecionados.")
    else:
        st.subheader("Distribuição Orçamental e Sazonalidade")
        c_left, c_right = st.columns([1.1, 0.9])

        with c_left:
            qtd_top = st.slider("Top órgãos a exibir no gráfico:", min_value=5, max_value=20, value=10)
            df_orgaos = (
                df.groupby('orgao')[tipo_metrica]
                .sum()
                .reset_index()
                .sort_values(by=tipo_metrica, ascending=False)
                .head(qtd_top)
            )

            fig_bar = px.bar(
                df_orgaos,
                x=tipo_metrica,
                y='orgao',
                orientation='h',
                title=f"Top {qtd_top} Órgãos por Volume Financeiro",
                labels={tipo_metrica: "Total (R$)", "orgao": "Órgão / Secretaria"},
                color=tipo_metrica,
                color_continuous_scale="Blues"
            )
            fig_bar.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title="Volume Acumulado (R$)",
                yaxis_title="",
                coloraxis_showscale=False,
                margin=dict(l=0, r=20, t=40, b=20),
                height=420
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with c_right:
            if 'mes_exercicio' in df.columns and 'ano_exercicio' in df.columns:
                df_tempo = df[df['mes_exercicio'].isin(range(1, 13))].copy()
                if not df_tempo.empty:
                    df_mes = (
                        df_tempo.groupby(['mes_exercicio', 'ano_exercicio'])[tipo_metrica]
                        .sum()
                        .reset_index()
                    )
                    df_mes['ano_exercicio'] = df_mes['ano_exercicio'].astype(str)
                    
                    fig_mes = px.line(
                        df_mes,
                        x='mes_exercicio',
                        y=tipo_metrica,
                        color='ano_exercicio',
                        markers=True,
                        title="Evolução Mensal das Despesas (2024 vs 2025)",
                        labels={'mes_exercicio': 'Mês', tipo_metrica: 'Total (R$)', 'ano_exercicio': 'Exercício'},
                        color_discrete_sequence=["#2563EB", "#F97316"]                  
                    )
                    fig_mes.update_xaxes(tickmode='linear', tick0=1, dtick=1)
                    fig_mes.update_layout(
                        margin=dict(l=20, r=20, t=40, b=20),
                        height=420,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_mes, use_container_width=True)
                else:
                    st.info("Dados de mês indisponíveis para visualização temporal.")

# -----------------------------------------------------------------------------
# ABA 2: AUDITORIA & CONTRATAÇÕES
# -----------------------------------------------------------------------------
with tab_auditoria:
    if df.empty:
        st.warning("⚠️ Nenhum registo coincide com os filtros selecionados.")
    else:
        st.subheader("Auditoria de Modalidades de Compra e Credores")
        col_lic, col_fav = st.columns(2)

        with col_lic:
            if 'tipolicitacao' in df.columns:
                df_lic = (
                    df.groupby('tipolicitacao')[tipo_metrica]
                    .sum()
                    .reset_index()
                    .sort_values(by=tipo_metrica, ascending=False)
                )
                fig_lic = px.pie(
                    df_lic.head(8),
                    names='tipolicitacao',
                    values=tipo_metrica,
                    title="Despesas por Modalidade de Licitação",
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Prism
                )
                fig_lic.update_traces(textposition='inside', textinfo='percent+label')
                fig_lic.update_layout(showlegend=False, height=380, margin=dict(t=40, b=20, l=10, r=10))
                st.plotly_chart(fig_lic, use_container_width=True)

        with col_fav:
            if 'favorecido' in df.columns:
                top_fornecedores = (
                    df.groupby('favorecido')[tipo_metrica]
                    .sum()
                    .reset_index()
                    .sort_values(by=tipo_metrica, ascending=False)
                    .head(10)
                )
                fig_fav = px.bar(
                    top_fornecedores,
                    x=tipo_metrica,
                    y='favorecido',
                    orientation='h',
                    title="Top 10 Favorecidos com Maior Volume Recebido",
                    labels={tipo_metrica: "Total (R$)", "favorecido": "Credor"},
                    color_discrete_sequence=["#0D9488"]
                )
                fig_fav.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    yaxis_title="",
                    xaxis_title="Total Recebido (R$)",
                    height=380,
                    margin=dict(t=40, b=20, l=10, r=10)
                )
                st.plotly_chart(fig_fav, use_container_width=True)

# -----------------------------------------------------------------------------
# ABA 3: RASTREABILIDADE & MICRODADOS
# -----------------------------------------------------------------------------
with tab_dados:
    st.subheader("Rastreabilidade Granular dos Registros Oficiais")
    st.caption("Extrato para auditoria detalhada com metadados do empenho, processo e credor.")

    if df.empty:
        st.warning("Nenhum registo para exibir.")
    else:
        cols_preview = [c for c in [
            'ano_exercicio', 'data', 'orgao', 'favorecido', tipo_metrica,
            'tipolicitacao', 'elementodespesa', 'documento', 'processo'
        ] if c in df.columns]

        st.dataframe(
            df[cols_preview].head(500),
            use_container_width=True,
            height=400
        )

        st.caption(f"A exibir amostra de 500 linhas de um total de {len(df):,} registos filtrados.")

        c_down1, c_down2 = st.columns([1, 3])
        with c_down1:
            csv_dados = df[cols_preview].to_csv(index=False, sep=";").encode('utf-8')
            st.download_button(
                label="📥 Descarregar Extrato Filtrado (CSV)",
                data=csv_dados,
                file_name="extrato_portal_transparencia_es.csv",
                mime="text/csv"
            )
        with c_down2:
            st.caption("O ficheiro gerado para download contém os dados exatos aplicados nos filtros laterais.")