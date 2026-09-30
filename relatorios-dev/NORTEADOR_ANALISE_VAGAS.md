# Norteador do Trabalho: Analise de Exigencia em Vagas Junior (2020-2026)

## 1) Objetivo do estudo

Avaliar se houve aumento de exigencia/cobranca em vagas junior ao longo do tempo (foco em 2020 a 2026), usando dados publicos de vagas e tecnicas de NLP + estatistica temporal.

---

## 2) Fonte principal de dados (GitHub Issues)

Repositorio principal:
- https://github.com/backend-br/vagas/issues

### Ponto tecnico importante
Issues NAO sao parte do historico de arquivos versionados, por isso nao aparecem em `git clone`.
A coleta correta deve ser feita via API do GitHub (REST ou GraphQL), e nao por download do repositorio.

### Coleta recomendada (automatica)

1. Usar endpoint REST de issues do repositorio:
   - `GET /repos/{owner}/{repo}/issues`
2. Paginar resultados (`per_page=100`) ate acabar.
3. Salvar no banco usando `issue.id` como chave unica (upsert).
4. Fazer atualizacao incremental diaria usando `updated_at`.
5. Usar token GitHub para aumentar limite de requests.

Exemplo de chamada REST:

```bash
curl -H "Accept: application/vnd.github+json" \
     -H "Authorization: Bearer $GITHUB_TOKEN" \
     "https://api.github.com/repos/backend-br/vagas/issues?state=all&per_page=100&page=1"
```

### Limites e boas praticas

- Sem token: ~60 req/h.
- Com token: ~5000 req/h.
- Evitar depender de scraping HTML.
- Evitar Search API para historico grande (limite de ~1000 resultados por busca).

### Funciona no Render?
Sim.

Arquitetura simples no Render:
- 1 Cron Job: ingestao diaria de vagas.
- 1 Web Service (opcional): API para dashboard.
- Banco PostgreSQL (Render Postgres ou externo).

---

## 3) Outras bases 100% gratuitas/publicas para complementar

## Fontes recomendadas

1. Outros repositorios de vagas no GitHub que usam Issues com padrao semelhante.
2. Hacker News "Who is hiring" via Algolia API (publica).
3. Arbeitnow API (confirmar politicas atuais antes do uso final).
4. Job boards publicos de Greenhouse e Lever (quando endpoint aberto).
5. Bases economicas de contexto (CAGED/IBGE) para enriquecer discussao de mercado.

### Estrategia metodologica para combinar fontes

- Definir uma base principal (backend-br/vagas).
- Usar bases adicionais para robustez, nao para misturar sem controle.
- Normalizar:
   - idioma
   - periodo
   - senioridade
   - area (backend/frontend/data etc.)

---

## 4) Pipeline recomendado (fim a fim)

## Etapa A - Ingestao

- Coletar issues com:
  - titulo
  - corpo
  - labels
  - data de criacao/atualizacao
  - estado
  - autor
- Persistir dados brutos.

## Etapa B - Limpeza e normalizacao

- Remover ruido de markdown/links.
- Padronizar texto para NLP.
- Filtrar apenas vagas relevantes (ex.: junior/estagio, se for o foco).

## Etapa C - Feature engineering de exigencia

Extrair sinais como:
- anos de experiencia exigidos
- numero de tecnologias obrigatorias
- mencao de cloud/k8s/microservicos/arquitetura
- exigencia de ingles
- exigencia de certificacoes/graducao
- termos de processo seletivo mais pesado (case, live coding, teste tecnico, multiplas etapas)

## Etapa D - Modelagem e analise temporal

- Criar um indice de exigencia por vaga (score continuo).
- Agregar por mes/trimestre/ano.
- Medir tendencia no tempo e possiveis quebras de regime.

## Etapa E - Dashboard

- Exibir tendencia de exigencia ao longo do tempo.
- Mostrar distribuicoes por periodo e por stack.
- Permitir filtros por senioridade, labels e ano.

---

## 5) ML/NLP: tecnicas recomendadas para o problema

## Baseline forte e explicavel

- `pandas` para preparo
- `regex` para extracao objetiva (anos, termos, certificacoes)
- `TF-IDF + Regressao Logistica` (classificacao de exigencia baixa/media/alta)

Vantagens:
- Rapido de implementar
- Facil de explicar em trabalho academico
- Bom ponto de comparacao

## Abordagem semantica avancada

- Embeddings com `sentence-transformers` (pt/en conforme dados)
- Opcional: BERTimbau para portugues

Usos:
- Capturar exigencias implicitas
- Melhorar classificacao de dificuldade quando texto e ambiguo

## Analise temporal e inferencia

- Teste de tendencia monotona (Mann-Kendall)
- Inclinacao robusta (Theil-Sen)
- Deteccao de mudanca estrutural (`ruptures`, PELT)

## Validacao cientifica (importante para banca)

- Rotular amostra manual (ex.: 300-1000 vagas)
- 2 avaliadores independentes
- Medir concordancia (`Cohen kappa`)
- Comparar baseline vs modelo avancado
- Reportar metricas (F1, ROC-AUC, MAE, conforme formulacao)

---

## 6) Como definir o "Indice de Exigencia"

Exemplo de formula inicial (ajustavel):

- +2.0 se exigir 2+ anos de experiencia
- +1.5 se exigir ingles
- +0.5 por tecnologia obrigatoria (limitado a 4)
- +1.0 se citar cloud/k8s/microservicos
- +1.0 se processo tiver case/live coding/teste tecnico multiplo
- +1.0 se houver mismatch (vaga junior com termos de pleno/senior)

Score final:
- Baixo: 0 a 2.0
- Medio: 2.1 a 4.0
- Alto: > 4.0

Observacao: os pesos podem ser calibrados com base na amostra rotulada manualmente.

---

## 7) Banco de dados sugerido

Tabela `jobs_raw`:
- `issue_id` (PK)
- `created_at`
- `updated_at`
- `title`
- `body`
- `labels_json`
- `source`

Tabela `jobs_features`:
- `issue_id` (FK)
- `years_required`
- `num_required_techs`
- `requires_english`
- `requires_cloud`
- `selection_hard_signals`
- `difficulty_score`
- `difficulty_class`

Tabela `jobs_timeseries` (opcional materializada):
- `period` (mes/trim)
- `avg_difficulty`
- `p50_difficulty`
- `n_jobs`

---

## 8) Streamlit para dashboard academico

Sim, Streamlit e adequado para entrega rapida e boa qualidade visual em contexto academico.

### Pontos fortes

- 100% Python (pipeline + ML + dashboard)
- Desenvolvimento rapido
- Facil deploy
- Boa integracao com Plotly/Altair

### Limites

- Menos flexivel que frontend dedicado para UX muito custom
- Escalabilidade inferior para produto multiusuario grande

Para TCC/projeto academico, costuma ser excelente custo-beneficio.

---

## 9) Stack recomendada (pratica)

- Coleta: `requests`, `httpx`, GitHub REST API
- ETL: `pandas`, `numpy`
- NLP/ML: `scikit-learn`, `spaCy`, `sentence-transformers`
- Estatistica temporal: `scipy`, `statsmodels`, `ruptures`
- Dashboard: `streamlit`, `plotly`
- Deploy: Render (Cron + Web + Postgres)

---

## 10) Roadmap de implementacao (4 semanas)

Semana 1:
- Implementar ingestao incremental GitHub
- Modelar banco e persistencia

Semana 2:
- Limpeza textual e extracao de features
- Definir score inicial de exigencia

Semana 3:
- Treinar baseline ML e validar com amostra rotulada
- Rodar analise temporal

Semana 4:
- Montar dashboard Streamlit
- Consolidar resultados, limitacoes e conclusoes

---

## 11) Riscos e mitigacoes

1. Viess de amostragem (somente vagas postadas em comunidades especificas)
   - Mitigar com 1-2 fontes extras e discussao metodologica.
2. Mudancas de formato no texto das vagas
   - Mitigar com extracao hibrida (regex + modelo).
3. Interpretacao de "dificuldade" subjetiva
   - Mitigar com rotulacao humana e metricas de concordancia.

---

## 12) Resultado esperado

Ao final, o trabalho deve responder com evidencia:
- Se a exigencia media em vagas junior aumentou de 2020 a 2026.
- Em quais dimensoes aumentou (experiencia, stack, processo seletivo, idioma etc.).
- Com qual nivel de confianca estatistica essa tendencia e sustentada.
