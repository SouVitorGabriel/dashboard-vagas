# PI4 - Prototipo inicial de analise de vagas junior

Este prototipo captura ate 100 issues de um repositorio GitHub de vagas, cria features de exigencia e gera visualizacoes no Streamlit.

## 1. Objetivo desta versao

- Provar o fluxo tecnico ponta a ponta.
- Entregar blocos visuais para relatorio parcial.
- Focar em vagas junior e textos em portugues.

## 2. O que ja foi implementado

- Coleta automatica de issues via API do GitHub (sem scraping HTML).
- Filtro para remover pull requests.
- Engenharia de features para indice de exigencia.
- Serie temporal e tendencia de exigencia.
- ML inicial:
  - clustering de texto (KMeans + SVD)
  - termos mais associados a maior exigencia (Logistic Regression)
- Dashboard Streamlit com graficos e tabela para relatorio.

## 3. Instalar e executar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Opcional para mais limite de API:

```bash
set GITHUB_TOKEN=seu_token
```

Executar dashboard:

```bash
streamlit run app.py
```

## 3.1 Deploy direto no Render (sem Python local)

Se voce vai subir no GitHub e conectar no Render, siga:

1. O projeto ja inclui o blueprint [render.yaml](render.yaml).
2. A versao do Python esta fixada em [.python-version](.python-version).
3. O passo a passo completo esta em [DEPLOY_RENDER.md](DEPLOY_RENDER.md).

Recomendacao:
- Configure GITHUB_TOKEN no Render para evitar rate limit da API.

## 4. Script rapido para gerar CSV da amostra

```bash
python scripts/fetch_sample_issues.py --owner backend-br --repo vagas --limit 100 --output data/issues_sample_features.csv
```

Alternativa sem Python (gera JSON bruto):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/fetch_sample_issues.ps1 -Owner backend-br -Repo vagas -Limit 100 -Output data/issues_sample_raw.json
```

Observacao:
- Durante esta implementacao foi gerada uma amostra real em `data/issues_sample_raw.json` com 99 issues.

## 5. Blocos recomendados no dashboard (alem da conclusao)

Para um foco academico em vagas junior BR/PT, estes blocos agregam valor:

1. Qualidade e recorte da amostra
   - total de issues capturadas
   - percentual identificado como junior
   - percentual em portugues
   - distribuicao por periodo

2. Sinais de cobranca por vaga
   - anos de experiencia exigidos
   - quantidade de tecnologias citadas
   - exigencia de ingles
   - sinais de processo seletivo mais pesado (case/teste/live coding)

3. Evolucao temporal
   - serie de exigencia media por mes
   - variacao percentual do inicio para o fim da serie
   - leitura da tendencia (aumento, queda ou estavel)

4. Estrutura da exigencia (insight qualitativo)
   - top tecnologias citadas
   - clusters de texto para grupos de perfil de vaga
   - termos associados a maior exigencia

5. Transparencia metodologica
   - formula do indice de exigencia
   - limitacoes do prototipo
   - proximos passos para validacao estatistica

## 6. Estrutura de arquivos

- app.py: dashboard Streamlit
- src/github_issues.py: coleta de issues na API GitHub
- src/features.py: feature engineering e score de exigencia
- src/ml_pipeline.py: blocos de ML e serie temporal
- scripts/fetch_sample_issues.py: exporta amostra para CSV

## 7. Proximos passos apos o prototipo

- Persistir dados em banco (PostgreSQL) com ingestao incremental.
- Criar rotulacao humana de amostra para validacao.
- Adicionar testes e monitoramento de qualidade dos dados.
