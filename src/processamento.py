import os
import zipfile
import glob
import pandas as pd

# 1. Definir caminhos das pastas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "dados", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "dados", "processed")

os.makedirs(PROCESSED_DIR, exist_ok=True)

def carregar_e_tratar_dados():
    print("🚀 Iniciando a ingestão dos dados...")
    
    # Buscar todos os ficheiros .zip na pasta dados/raw/
    zip_files = glob.glob(os.path.join(RAW_DIR, "*.zip"))
    
    dfs = []
    
    for zip_path in zip_files:
        print(f"📦 Processando: {os.path.basename(zip_path)}")
        with zipfile.ZipFile(zip_path, 'r') as z:
            for filename in z.namelist():
                # Processar apenas ficheiros CSV ou TXT dentro do zip
                if filename.endswith('.csv') or filename.endswith('.txt'):
                    with z.open(filename) as f:
                        # Leitura com Pandas (ajuste sep e encoding se necessário)
                        df_temp = pd.read_csv(f, sep=';', encoding='utf-8', low_memory=False)
                        dfs.append(df_temp)
    
    if not dfs:
        print("❌ Nenhum ficheiro válido encontrado nos .zip.")
        return
    
    # Unificar todos os dataframes em um só
    df = pd.concat(dfs, ignore_index=True)
    print(f"📊 Total de registros brutos importados: {len(df):,}")
    
    # -------------------------------------------------------------
    # 2. LIMPEZA E TRATAMENTO DE DADOS (Atendendo aos requisitos)
    # -------------------------------------------------------------
    
    # A. Padronização do nome das colunas (caixa baixa e sem espaços)
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    
    # B. Remoção de duplicados exatos
    duplicados = df.duplicated().sum()
    if duplicados > 0:
        df = df.drop_duplicates()
        print(f"🧹 Registros duplicados removidos: {duplicados:,}")
        
    # C. Tratamento de campos de valores (substituir vírgulas por pontos se forem strings)
    colunas_valor = [c for c in df.columns if 'valor' in c or 'pago' in c or 'empenho' in c]
    for col in colunas_valor:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
    # D. Tratamento de datas (se houver coluna de data)
    colunas_data = [c for c in df.columns if 'data' in c]
    for col in colunas_data:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # E. Preenchimento de campos de texto ausentes/nulos
    colunas_texto = df.select_dtypes(include=['object']).columns
    df[colunas_texto] = df[colunas_texto].fillna("NÃO INFORMADO")

    print(f"✅ Tratamento concluído! Registros finais: {len(df):,}")
    
    # -------------------------------------------------------------
    # 3. EXPORTAÇÃO DA BASE PROCESSADA
    # -------------------------------------------------------------
    output_file = os.path.join(PROCESSED_DIR, "despesas_es_consolidado.csv")
    df.to_csv(output_file, index=False, sep=';', encoding='utf-8')
    print(f"💾 Ficheiro processado salvo em: {output_file}")

if __name__ == "__main__":
    carregar_e_tratar_dados()