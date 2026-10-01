import os
import zipfile
import glob
import logging
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DE LOGS (Critério de Engenharia do Edital)
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "dados", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "dados", "processed")

os.makedirs(PROCESSED_DIR, exist_ok=True)

# Colunas essenciais selecionadas do leiaute oficial para a POC
COLUNAS_ALVO = [
    'ano', 'data', 'valorpago', 'valorliquidado', 'valorempenho', 'valorrap',
    'orgao', 'unidadegestora', 'favorecido', 'cpfcnpjnis', 'tipolicitacao',
    'elementodespesa', 'subelementodespesa', 'funcao', 'programa',
    'historicodocumento', 'documento', 'processo'
]


def identificar_separador(arquivo_obj) -> str:
    """Detecta se o arquivo CSV é delimitado por ponto e vírgula ou vírgula."""
    posicao = arquivo_obj.tell()
    linha_cabecalho = arquivo_obj.readline().decode('latin1', errors='ignore')
    arquivo_obj.seek(posicao)
    return ';' if linha_cabecalho.count(';') >= linha_cabecalho.count(',') else ','


def limpar_e_processar_dados():
    logging.info("🚀 Iniciando Pipeline de Ingestão e Limpeza de Dados da CP2...")

    zip_files = glob.glob(os.path.join(RAW_DIR, "*.zip"))

    if not zip_files:
        logging.error("❌ Nenhum arquivo .zip encontrado na pasta 'dados/raw/'.")
        logging.info("Copie os arquivos compactados das despesas de 2024/2025 para 'dados/raw/'.")
        return False

    dfs = []

    # -------------------------------------------------------------------------
    # ETAPA 1: LEITURA RESILIENTE DOS ZIPS
    # -------------------------------------------------------------------------
    for zip_path in zip_files:
        nome_zip = os.path.basename(zip_path)
        logging.info(f"📦 Lendo arquivo compactado: {nome_zip}")

        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                for filename in z.namelist():
                    if (filename.endswith('.csv') or filename.endswith('.txt')) and not filename.startswith('__MACOSX'):
                        with z.open(filename) as f:
                            sep = identificar_separador(f)
                            
                            try:
                                df_temp = pd.read_csv(f, sep=sep, encoding='utf-8', low_memory=False)
                            except UnicodeDecodeError:
                                df_temp = pd.read_csv(f, sep=sep, encoding='latin1', low_memory=False)

                            # Normalizar nomes de colunas logo na leitura
                            df_temp.columns = [c.strip().lower().replace(" ", "_") for c in df_temp.columns]

                            # Manter apenas as colunas de interesse
                            cols_disponiveis = [c for c in COLUNAS_ALVO if c in df_temp.columns]
                            df_temp = df_temp[cols_disponiveis]

                            dfs.append(df_temp)
                            logging.info(f"   -> Extraído '{filename}': {len(df_temp):,} linhas")
        except Exception as e:
            logging.error(f"⚠️ Erro ao abrir {nome_zip}: {e}")

    if not dfs:
        logging.error("❌ Nenhum dado tabular válido pôde ser extraído dos arquivos zip.")
        return False

    # -------------------------------------------------------------------------
    # ETAPA 2: CONCATENAÇÃO EM MEMÓRIA
    # -------------------------------------------------------------------------
    logging.info("Unificando bases de dados carregadas...")
    df = pd.concat(dfs, ignore_index=True)
    logging.info(f"Total bruto de registros importados: {len(df):,} linhas.")

    # -------------------------------------------------------------------------
    # ETAPA 3: FILTRAGEM POR EXERCÍCIO (2024 e 2025)
    # -------------------------------------------------------------------------
    if 'ano' in df.columns:
        logging.info("Filtrando estritamente os exercícios fiscais do edital (2024 e 2025)...")
        df['ano'] = pd.to_numeric(df['ano'], errors='coerce')
        df = df[df['ano'].isin([2024, 2025])]
        df['ano'] = df['ano'].astype(int)
        df.rename(columns={'ano': 'ano_exercicio'}, inplace=True)

    # -------------------------------------------------------------------------
    # ETAPA 4: DEDUPLICAÇÃO
    # -------------------------------------------------------------------------
    duplicados = df.duplicated().sum()
    if duplicados > 0:
        df = df.drop_duplicates()
        logging.info(f"🧹 Registros duplicados exatos removidos: {duplicados:,}")

    # -------------------------------------------------------------------------
    # ETAPA 5: CONVERSÃO DE VALORES MONETÁRIOS (com suporte a estornos negativos)
    # -------------------------------------------------------------------------
    colunas_moeda = [c for c in ['valorpago', 'valorliquidado', 'valorempenho', 'valorrap'] if c in df.columns]

    for col in colunas_moeda:
        logging.info(f"Convertendo coluna monetária: {col}")
        if df[col].dtype == 'object':
            df[col] = (
                df[col]
                .astype(str)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].fillna(0.0).round(2)

    # -------------------------------------------------------------------------
    # ETAPA 6: TRATAMENTO DE DATAS E CRIAÇÃO DO MÊS
    # -------------------------------------------------------------------------
    if 'data' in df.columns:
        logging.info("Padronizando datas e extraindo mês para análises sazonais...")
        df['data_formatada'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
        df['mes_exercicio'] = df['data_formatada'].dt.month.fillna(0).astype(int)
        df['data'] = df['data_formatada'].dt.strftime('%d/%m/%Y').fillna('NÃO INFORMADO')
        df.drop(columns=['data_formatada'], inplace=True, errors='ignore')

    # -------------------------------------------------------------------------
    # ETAPA 7: TRATAMENTO DE TEXTOS E AUDITORIA (LGPD E NULOS)
    # -------------------------------------------------------------------------
    colunas_texto = df.select_dtypes(include=['object']).columns
    for col in colunas_texto:
        df[col] = df[col].fillna("NÃO INFORMADO").astype(str).str.strip().str.upper()

    # Forçar explicitamente as colunas de órgãos como string
    if 'orgao' in df.columns:
        df['orgao'] = df['orgao'].fillna("NÃO INFORMADO").astype(str).str.strip().str.upper()

    if 'unidadegestora' in df.columns:
        df['unidadegestora'] = df['unidadegestora'].fillna("NÃO INFORMADO").astype(str).str.strip().str.upper()

    # Preencher código numérico com a descrição por extenso da unidade gestora
    if 'orgao' in df.columns and 'unidadegestora' in df.columns:
        mascara_substituicao = (
            (df['orgao'] == "NÃO INFORMADO") |
            (df['orgao'].str.isnumeric()) |
            (df['orgao'] == "")
        )
        df['orgao'] = np.where(mascara_substituicao, df['unidadegestora'], df['orgao'])

    # -------------------------------------------------------------------------
    # ETAPA 8: EXPORTAÇÃO CONSOLIDADA E OTIMIZADA
    # -------------------------------------------------------------------------
    output_path = os.path.join(PROCESSED_DIR, "despesas_es_consolidado.csv")
    logging.info(f"💾 Salvando base consolidada otimizada com {len(df):,} linhas...")
    
    df.to_csv(output_path, index=False, sep=";", encoding="utf-8")
    logging.info(f"✅ Sucesso! Base pronta para o Streamlit em: {output_path}")
    return True


if __name__ == "__main__":
    limpar_e_processar_dados()