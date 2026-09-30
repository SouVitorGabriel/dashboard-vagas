# Guia de Deploy no Render (sem Python local)

Este projeto ja esta preparado para deploy no Render usando o arquivo render.yaml.

## 1) O que ja esta pronto no projeto

- Dependencias em requirements.txt
- Comando de inicializacao para Streamlit no Render
- Versao de Python definida em .python-version e render.yaml
- Blueprint de deploy em render.yaml

## 2) Publicar no GitHub

1. Crie um repositorio no GitHub (se ainda nao existir).
2. Faca commit dos arquivos do projeto.
3. Envie para branch main.

## 3) Deploy no Render com Blueprint

1. No painel do Render, clique em New +.
2. Selecione Blueprint.
3. Conecte sua conta GitHub e selecione o repositorio.
4. O Render detectara o arquivo render.yaml automaticamente.
5. Confirme a criacao do servico web.

## 4) Variaveis de ambiente obrigatorias/recomendadas

Configure no servico Render em Environment:

1. GITHUB_TOKEN (recomendado)
   - Sem token, o limite da API do GitHub e baixo.
   - Com token, o dashboard fica mais estavel para coleta.
2. STREAMLIT_BROWSER_GATHER_USAGE_STATS=false (ja definido no blueprint)
3. PYTHON_VERSION=3.12.6 (ja definido no blueprint)

## 5) Comandos usados no Render

Build command:
- pip install --upgrade pip && pip install -r requirements.txt

Start command:
- streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true

## 6) Teste pos-deploy

1. Abra a URL publica gerada pelo Render.
2. Verifique se os cards de metricas carregam.
3. Clique em Atualizar coleta no menu lateral.
4. Confirme exibicao de:
   - serie temporal
   - distribuicao de exigencia
   - top tecnologias
   - clusters de texto

## 7) Problemas comuns

1. Erro de rate limit da API GitHub
   - Solucao: configurar GITHUB_TOKEN no Render.
2. Erro de inicializacao por dependencia
   - Solucao: verificar requirements.txt e fazer manual deploy novamente.
3. Falha no health check
   - Solucao: confirmar healthCheckPath /_stcore/health e start command.

## 8) Observacao sobre persistencia

A v0.0.1 e um prototipo sem banco relacional. Os dados sao coletados na execucao da aplicacao.
Para v0.0.2, recomenda-se adicionar PostgreSQL + ingestao incremental via job agendado no Render.
