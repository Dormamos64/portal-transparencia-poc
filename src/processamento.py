import os
import zipfile
import glob
import pandas as pd
import numpy as np

# 1. Definir caminhos de diretorias (baseados na localização do script)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "dados", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "dados", "processed")

# Criar pasta processed se não existir
os.makedirs(PROCESSED_DIR, exist_ok=True)

def limpar_e_processar_dados():
    print("🚀 A iniciar a Ingestão e Tratamento de Dados da CP2...")
    
    # Procurar todos os ficheiros .zip dentro de dados/raw/
    zip_files = glob.glob(os.path.join(RAW_DIR, "*.zip"))
    
    if not zip_files:
        print("❌ Nenhum ficheiro .zip encontrado na pasta 'dados/raw/'. Verifique os ficheiros!")
        return

    dfs = []
    
    # -------------------------------------------------------------
    # ETAPA 1: LEITURA DOS FICHEIROS ZIP
    # -------------------------------------------------------------
    for zip_path in zip_files:
        nome_zip = os.path.basename(zip_path)
        print(f"📦 A ler: {nome_zip}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                for filename in z.namelist():
                    # Filtrar ficheiros de dados (.csv, .txt) ignorando pastas ocultas
                    if (filename.endswith('.csv') or filename.endswith('.txt')) and not filename.startswith('__MACOSX'):
                        with z.open(filename) as f:
                            # Tentar leitura com separador ponto e vírgula e encoding UTF-8
                            try:
                                df_temp = pd.read_csv(f, sep=';', encoding='utf-8', low_memory=False)
                            except UnicodeDecodeError:
                                df_temp = pd.read_csv(f, sep=';', encoding='latin1', low_memory=False)
                            
                            dfs.append(df_temp)
        except Exception as e:
            print(f"⚠️ Erro ao abrir {nome_zip}: {e}")

    if not dfs:
        print("❌ Nenhum dado válido extraído dos ficheiros zip.")
        return

    # Unificar todos os pedaços num único DataFrame
    df = pd.concat(dfs, ignore_index=True)
    print(f"📊 Total de registos brutos importados: {len(df):,}")

    # -------------------------------------------------------------
    # ETAPA 2: PADRONIZAÇÃO DE COLUNAS
    # -------------------------------------------------------------
    # Remover espaços extras e colocar nomes de colunas em minúsculas
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # -------------------------------------------------------------
    # ETAPA 3: REMOÇÃO DE DUPLICADOS E REGISTOS INVÁLIDOS
    # -------------------------------------------------------------
    duplicados_iniciais = df.duplicated().sum()
    if duplicados_iniciais > 0:
        df = df.drop_duplicates()
        print(f"🧹 Registos duplicados exatos removidos: {duplicados_iniciais:,}")

    # -------------------------------------------------------------
    # ETAPA 4: TRATAMENTO DE VALORES MONETÁRIOS
    # -------------------------------------------------------------
    # Mapear colunas que contêm valores (pago, empenhado, valor, etc.)
    colunas_valor = [c for c in df.columns if any(p in c for p in ['valor', 'pago', 'empenho', 'liquidado'])]
    
    for col in colunas_valor:
        if df[col].dtype == 'object':
            # Formatar strings do padrão brasileiro (1.000,00 -> 1000.00)
            df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Preencher valores ausentes com 0.0
        df[col] = df[col].fillna(0.0)

    # -------------------------------------------------------------
    # ETAPA 5: TRATAMENTO DE DATAS (CORREÇÃO DO ANO 1970)
    # -------------------------------------------------------------
    colunas_data = [c for c in df.columns if 'data' in c or 'emissao' in c]
    
    col_data_principal = colunas_data[0] if colunas_data else None

    if col_data_principal:
        print(f"📅 A tratar coluna de data: '{col_data_principal}'...")
        # Converter para formato de data do Pandas (erros viram NaT/Nulos em vez de 1970)
        df['data_processada'] = pd.to_datetime(df[col_data_principal], errors='coerce', dayfirst=True)
        
        # Extrair o ano do exercício
        df['ano_exercicio'] = df['data_processada'].dt.year
        
        # FILTRO RÍGIDO: Manter APENAS registos com anos válidos do edital (2024 e 2025)
        df = df[df['ano_exercicio'].isin([2024, 2025])]
        df['ano_exercicio'] = df['ano_exercicio'].astype(int)
    else:
        print("⚠️ Nenhuma coluna explícita de data encontrada. Verifique as colunas do dataset.")

    # -------------------------------------------------------------
    # ETAPA 6: TRATAMENTO DE TEXTOS E NULOS
    # -------------------------------------------------------------
    colunas_texto = df.select_dtypes(include=['object']).columns
    for col in colunas_texto:
        df[col] = df[col].fillna("NÃO INFORMADO").astype(str).str.strip().str.upper()

    # -------------------------------------------------------------
    # ETAPA 7: EXPORTAÇÃO DA BASE FINAL
    # -------------------------------------------------------------
    output_path = os.path.join(PROCESSED_DIR, "despesas_es_consolidado.csv")
    print(f"💾 A guardar ficheiro tratado final com {len(df):,} registos...")
    
    df.to_csv(output_path, index=False, sep=";", encoding="utf-8")
    print(f"✅ Sucesso! Ficheiro gerado em: {output_path}")

if __name__ == "__main__":
    limpar_e_processar_dados()