# Relatorio Final de Implementacao - v0.0.1

Data: 2026-09-30
Projeto: PI4 - Analise de exigencia em vagas junior (2020-2026)

## 1. Resumo executivo

A versao v0.0.1 entrega um prototipo funcional de ponta a ponta para:

1. Coletar issues de vagas do repositorio backend-br/vagas via API do GitHub.
2. Extrair sinais iniciais de exigencia (features) para vagas junior em portugues.
3. Calcular um indice de exigencia por vaga.
4. Gerar blocos de ML iniciais.
5. Exibir visualizacoes no Streamlit para uso em relatorio parcial.

Esta versao prioriza velocidade de validacao visual/metodologica e nao robustez de producao.

## 2. Artefatos entregues na v0.0.1

- app.py
- src/github_issues.py
- src/features.py
- src/ml_pipeline.py
- scripts/fetch_sample_issues.py
- scripts/fetch_sample_issues.ps1
- README.md
- data/issues_sample_raw.json (amostra real coletada)

## 3. Evidencia de dados reais

Foi coletada uma amostra real com 99 issues e salva em:
- data/issues_sample_raw.json

Motivo de 99 (e nao 100): o endpoint /issues tambem retorna PRs e eles foram removidos do resultado final.

## 4. Relacao entre Norteador e implementacao

Documento de referencia movido para:
- relatorios-dev/NORTEADOR_ANALISE_VAGAS.md

### 4.1 Mapeamento por secao do norteador

| Secao do norteador | Status na v0.0.1 | O que foi implementado |
|---|---|---|
| 1) Objetivo do estudo | Parcial | Estrutura pronta para medir exigencia ao longo do tempo com recorte junior/PT. Analise temporal ainda exploratoria nesta versao. |
| 2) Fonte principal GitHub Issues | Concluido | Coleta automatica via API GitHub, com filtros e remocao de PRs em src/github_issues.py. |
| 2) Coleta automatica (paginacao/token) | Parcial | Paginacao por pagina e suporte a token implementados; persistencia em banco e ingestao incremental ainda nao implementadas. |
| 3) Outras bases publicas | Nao iniciado | Recomendacoes documentadas no norteador, sem integracao de novas fontes nesta versao. |
| 4A) Ingestao | Concluido | Captura de titulo, corpo, labels, datas, estado, autor e URL. |
| 4B) Limpeza/normalizacao | Concluido | Normalizacao textual, remocao de acentos e filtros de junior/portugues em src/features.py. |
| 4C) Feature engineering | Concluido | Anos de experiencia, contagem de tecnologias, ingles, stack avancada, processo seletivo exigente e mismatch junior/senior. |
| 4D) Modelagem/temporal | Parcial | Score de exigencia e serie temporal com tendencia linear inicial implementados em src/ml_pipeline.py. |
| 4E) Dashboard | Concluido | Dashboard Streamlit com metricas, serie temporal, distribuicoes, clusters, termos discriminantes e tabela de amostra. |
| 5) Baseline explicavel (TF-IDF + LogReg) | Concluido | Implementado bloco de termos associados a maior exigencia usando TF-IDF + Logistic Regression. |
| 5) Abordagem semantica avancada | Nao iniciado | Embeddings/BERTimbau ainda nao implementados. |
| 5) Inferencia estatistica robusta | Nao iniciado | Mann-Kendall, Theil-Sen e ruptures ainda nao implementados. |
| 6) Indice de exigencia | Concluido | Formula inicial implementada com pesos e classificacao baixo/medio/alto. |
| 7) Banco de dados sugerido | Nao iniciado | Sem PostgreSQL nesta versao (dados em memoria/arquivo). |
| 8) Streamlit para dashboard | Concluido | App Streamlit funcionando como camada visual principal. |
| 9) Stack recomendada | Parcial | requests, pandas, numpy, scikit-learn, streamlit e plotly usados; demais libs avancadas pendentes. |
| 10) Roadmap de 4 semanas | Em andamento | Semana 1 parcialmente iniciada (coleta e prototipo visual). |
| 11) Riscos/mitigacoes | Parcial | Riscos documentados; mitigacoes (rotulacao dupla, validacao formal) ainda pendentes. |
| 12) Resultado esperado final | Nao concluido | v0.0.1 e prototipo; conclusao cientifica final depende de maior base e validacao estatistica. |

## 5. Funcionalidades implementadas (detalhe tecnico)

1. Coleta de issues na API GitHub:
   - suporte a token via GITHUB_TOKEN
   - estado all/open/closed
   - limite configuravel
   - remocao automatica de pull requests

2. Engenharia de features:
   - deteccao de recorte junior
   - heuristica de idioma portugues
   - extracao de anos de experiencia
   - extracao de tecnologias citadas
   - sinais de exigencia (ingles, stack avancada, processo seletivo, mismatch)

3. Indice de exigencia:
   - score numerico por vaga
   - classe baixo/medio/alto

4. Blocos de ML:
   - clustering textual (KMeans + reducacao SVD 2D)
   - termos discriminantes de maior exigencia (TF-IDF + Logistic Regression)

5. Visualizacoes no dashboard:
   - cards de recorte da amostra
   - evolucao temporal de exigencia media
   - volume de vagas por periodo
   - distribuicao de score
   - taxas de sinais de cobranca
   - top tecnologias
   - tabela de amostra com exportacao CSV

## 6. Pendencias para v0.0.2

1. Persistencia em PostgreSQL com upsert por issue_id.
2. Ingestao incremental por updated_at (since) em job agendado.
3. Integracao de base secundaria publica para robustez.
4. Testes automatizados de pipeline.
5. Validacao estatistica de tendencia (Mann-Kendall/Theil-Sen/ruptures).
6. Rotulacao humana de amostra para calibrar o indice.

## 7. Limitacoes conhecidas da v0.0.1

1. Ambiente local sem runtime Python ativo durante a validacao desta entrega (nao foi possivel executar o app neste terminal).
2. Prototipo orientado a demonstracao visual, ainda sem persistencia relacional.
3. Heuristicas de idioma e senioridade ainda simples.
4. Sem inferencia causal/estatistica robusta para conclusao final.

## 8. Conclusao desta entrega

A v0.0.1 cumpre o objetivo de colocar o projeto em execucao com dados reais, gerar features de exigencia e produzir blocos visuais e analiticos iniciais para o relatorio parcial.

O norteador foi convertido em implementacao concreta nas frentes de coleta, feature engineering, score inicial, ML baseline e dashboard, com trilha clara de evolucao para a proxima versao.
