# 🏛️ Portal da Transparência Inteligente — Espírito Santo (PTI-ES)
> Prova de Conceito (POC) — Simulação de CPSI (Contrato Público para Solução Inovadora)[cite: 1]
> FIAP | Bacharelado em Engenharia de Software | Checkpoint 2 (CP2)[cite: 1]

---

## 📌 1. Visão Geral da Solução

O Portal da Transparência Inteligente (PTI-ES) é uma plataforma analítica desenvolvida para transformar dados brutos e complexos da execução orçamentária do Governo do Estado do Espírito Santo (exercícios fiscais de 2024 e 2025) em inteligência compreensível, ágil e auditável[cite: 1, 3].

A solução soluciona o desafio da assimetria de informação nos portais públicos, que disponibilizam volumes massivos de lançamentos contábeis (mais de 1 milhão de registros e dezenas de atributos técnicos) sem ferramentas adequadas para a exploração rápida por cidadãos, jornalistas e auditores[cite: 3].

---

## 👥 2. Público-Alvo e Proposta de Valor

* Público Prioritário: Jornalistas de investigação cívica, pesquisadores acadêmicos, analistas de órgãos de controle e cidadãos[cite: 3].
* Problema Central: Dificuldade em cruzar rapidamente fornecedores, valores empenhados/pagos, modalidades de contratação e sazonalidade de gastos públicos em bases volumosas[cite: 2, 3].
* Proposta de Valor: Centralizar a análise em indicadores agregados de alto impacto, possibilitar a triagem imediata de contratos por porte financeiro (curva de Pareto), auditar modalidades de compra pública e disponibilizar a exportação com rastreabilidade granular dos registros oficiais[cite: 2, 3, 4].

---

## 🏗️ 3. Arquitetura da Solução e Estrutura de Diretórios

O projeto segue princípios de Engenharia de Software focados em separação de responsabilidades, modularidade e reprodutibilidade de dados[cite: 4, 7]:

```text
portal-transparencia-poc/
│
├── dados/
│   ├── raw/                 # Diretório para os arquivos comprimidos (.zip) originais
│   └── processed/           # Base tratada e consolidada (gerada pelo pipeline)
│
├── src/
│   └── processamento.py     # Script de ETL: ingestão, limpeza, tipagem e deduplicação
│
├── tests/
│   └── test_pipeline.py     # Suíte de testes automatizados com validação contábil
│
├── app.py                   # Interface interativa e painel analítico (Streamlit)
├── requirements.txt         # Especificação de dependências com versões testadas
├── .gitignore               # Regras de exclusão de dados pesados e temporários
└── README.md                # Documentação técnica e guia operacional do sistema
```
Tecnologias e Bibliotecas Empregadas:
* Linguagem Base: Python 3.10 ou superior
* Ingestão e Manipulação: Pandas, NumPy
* Visualização Gráfica Interativa: Plotly Express
* Interface de Usuário (Frontend): Streamlit
* Qualidade e Testes Unitários: Pytest[cite: 4, 7]
* Controle de Versões: Git / GitHub[cite: 4]

---

## ⚙️ 4. Guia Passo a Passo: Instalação e Configuração

Execute os passos abaixo diretamente no terminal integrado do VS Code (PowerShell, Bash ou Zsh) na raiz do projeto[cite: 4, 5]:

Passo 4.1: Clonar o Repositório
git clone https://github.com/Dormamos64/portal-transparencia-poc.git
cd portal-transparencia-poc

Passo 4.2: Criar e Ativar o Ambiente Virtual

* No Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1

* No Linux ou macOS:
python3 -m venv venv
source venv/bin/activate

Passo 4.3: Instalar as Dependências do Projeto
Com o ambiente ativado, instale todos os pacotes necessários:
pip install -r requirements.txt

---

## 📥 5. Ingestão e Processamento dos Dados Oficiais (ETL)

Por boas práticas de governança de código em repositórios remotos, arquivos de dados volumosos (.zip e .csv) não são versionados pelo Git[cite: 4]. O carregamento da base obedece estritamente ao seguinte fluxo:

Passo 5.1: Obtenção dos Arquivos Compactados
1. Baixe os arquivos compactados oficiais contendo os microdados de despesas públicas dos anos de 2024 e 2025 do Portal da Transparência do Governo do Estado do Espírito Santo (ou os arquivos disponibilizados na atividade da FIAP)[cite: 3].
2. Mantenha os arquivos no formato compactado original .zip.

Passo 5.2: Alocação no Diretório Bruto
Copie e cole todos os arquivos compactados .zip diretamente dentro do diretório dados/raw/ do projeto:
portal-transparencia-poc/dados/raw/*.zip

Passo 5.3: Execução do Pipeline de Tratamento
No terminal, execute o pipeline de ETL a partir da raiz do projeto:
python src/processamento.py

O que o pipeline realiza de forma automatizada:
1. Detecção dinâmica de separador e encoding: Lê os arquivos dentro dos .zip identificando automaticamente ';' ou ',', com suporte a encodings UTF-8 e Latin-1.
2. Seleção estratégica de atributos: Reduz mais de 70 colunas originais para as colunas essenciais da POC, economizando memória RAM e acelerando a interface.
3. Conversão monetária precisa: Converte strings no padrão brasileiro com 4 casas decimais para float e preserva valores negativos (estornos contábeis de liquidação).
4. Normalização temporal: Trata as datas, extrai o mês fiscal e assegura o filtro estrito para os exercícios de 2024 e 2025[cite: 3, 4].
5. Deduplicação e tratamento de texto: Remove linhas duplicadas e preenche nulos com a menção NÃO INFORMADO.
6. Exportação consolidada: Salva a base tratada em dados/processed/despesas_es_consolidado.csv.

---

## 🖥️ 6. Executando a Aplicação Web (POC)

Com o arquivo despesas_es_consolidado.csv devidamente gerado em dados/processed/, inicie a interface:

streamlit run app.py

O dashboard analítico será aberto no navegador padrão no endereço:
http://localhost:8501

Funcionalidades Disponíveis no Painel:
* Seleção da Métrica Contábil: Alternância instantânea entre Valor Pago, Valor Liquidado e Valor Empenhado[cite: 3].
* Filtros Multidimensionais: Seleção de anos de exercício, lista de órgãos públicos ordenada por volume gasto, isolamento por faixas de porte financeiro e busca textual por fornecedor ou CNPJ[cite: 3].
* Aba 1 (Panorama Executivo): Indicadores principais (Volume total, transações, ticket médio, maior despesa), ranking gráfico dos maiores órgãos e gráfico de linha comparativo da sazonalidade mensal (2024 vs 2025)[cite: 3].
* Aba 2 (Auditoria & Contratações): Distribuição percentual das modalidades de contratação (Pregão, Dispensa, Inexigibilidade) e ranking dos 10 fornecedores com maior volume recebido[cite: 3].
* Aba 3 (Rastreabilidade & Microdados): Tabela de auditoria dos registros oficiais com metadados do documento de pagamento, processo administrativo e botão para exportar o extrato filtrado em CSV[cite: 3, 4].

---

## 🧪 7. Suíte de Testes Automatizados

O projeto inclui testes de unidade com pytest para assegurar a confiabilidade das regras contábeis e do pipeline[cite: 4, 7].

Para rodar os testes, execute na raiz do projeto:

python -m pytest

Casos de Teste Verificados:
* test_conversao_valores_positivos_e_decimais: Validação da conversão de strings monetárias com milhar e 4 casas decimais para float.
* test_tratamento_valores_negativos_estorno: Garantia de integridade matemática para estornos contábeis negativos sem quebrar cálculos.
* test_tratamento_valores_invalidos_ou_nulos: Resiliência contra traços, nulos ou strings inválidas, garantindo retorno 0.0.
* test_filtro_exercicios_edital: Conformidade da regra fiscal que retém estritamente os anos de 2024 e 2025[cite: 3].

---

## ⚖️ 8. Governança, LGPD e Princípios Éticos

* Privacidade e LGPD: Os dados processados provêm do Portal da Transparência do Espírito Santo. Identificadores de pessoas físicas (CPF) já chegam ofuscados na fonte (###.***.***-##), evitando a exposição indevida de dados pessoais[cite: 4].
* Isenção de Juízo Automático: Conforme previsto no edital, modalidades como dispensa ou inexigibilidade não são tratadas pelo software como prova automática de irregularidade, mas sim como fatos contábeis oficiais registrados[cite: 4].
* Limitações Técnicas Conhecidas: A POC opera sobre os exercícios oficiais de 2024 e 2025[cite: 3, 4]. Eventuais inconsistências de preenchimento oriundas do próprio sistema estadual são identificadas com a menção NÃO INFORMADO.
