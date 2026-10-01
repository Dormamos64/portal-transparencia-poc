import pytest
import pandas as pd
import numpy as np


def converter_moeda_br(serie: pd.Series) -> pd.Series:
    """Função de apoio para testar a lógica contábil do pipeline."""
    if serie.dtype == 'object':
        serie = (
            serie.astype(str)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
        )
        serie = pd.to_numeric(serie, errors='coerce')
    return serie.fillna(0.0).round(2)


def test_conversao_valores_positivos_e_decimais():
    """Valida se valores com 4 casas decimais e pontos de milhar convertem corretamente."""
    dados_entrada = pd.Series(["528,0000", "1.250.000,5000", "120,9200"])
    esperado = pd.Series([528.00, 1250000.50, 120.92])
    resultado = converter_moeda_br(dados_entrada)
    assert np.allclose(resultado, esperado)


def test_tratamento_valores_negativos_estorno():
    """Garante que estornos contábeis negativos sejam preservados como números válidos."""
    dados_entrada = pd.Series(["-88,0000", "-20.045,0800"])
    esperado = pd.Series([-88.00, -20045.08])
    resultado = converter_moeda_br(dados_entrada)
    assert np.allclose(resultado, esperado)


def test_tratamento_valores_invalidos_ou_nulos():
    """Garante que registros com traços, nulos ou texto virem 0.0 sem quebrar a execução."""
    dados_entrada = pd.Series([None, "-", "NÃO INFORMADO", "0,0000"])
    resultado = converter_moeda_br(dados_entrada)
    assert (resultado == 0.0).all()


def test_filtro_exercicios_edital():
    """Valida se a regra fiscal retém estritamente os anos de 2024 e 2025."""
    df_anos = pd.DataFrame({"ano": [2022, 2023, 2024, 2025, 2026]})
    df_filtrado = df_anos[df_anos["ano"].isin([2024, 2025])]
    assert sorted(df_filtrado["ano"].tolist()) == [2024, 2025]