# Entregaveis da atividade

Esta pasta concentra os arquivos necessarios para avaliacao do experimento de
metricas de pipeline CI/CD.

## Links principais

- Repositorio: <https://github.com/Rafaelfurtadovs/ponderada_pipeline>
- Workflow GitHub Actions: <https://github.com/Rafaelfurtadovs/ponderada_pipeline/blob/main/.github/workflows/ci-metrics.yml>
- Execucoes reais: <https://github.com/Rafaelfurtadovs/ponderada_pipeline/actions/workflows/ci-metrics.yml>
- Relatorio tecnico: <https://github.com/Rafaelfurtadovs/ponderada_pipeline/blob/main/entregaveis/relatorio_tecnico.md>
- Run com falha proposital: <https://github.com/Rafaelfurtadovs/ponderada_pipeline/actions/runs/26888817920>

## Conteudo da pasta

- `relatorio_tecnico.md`: relatorio completo com analise, links dos runs,
  commits reais, variacoes, resultados inesperados e limitacoes.
- `workflow/ci-metrics.yml`: arquivo YAML do GitHub Actions.
- `scripts/collect_metrics.py`: script proprio de coleta das metricas via API do
  GitHub.
- `scripts/generate_charts.py`: script de geracao dos graficos.
- `scripts/set_scenario.py`: script usado para controlar as variacoes dos runs.
- `scripts/summarize_tests.py`: script usado pelo pipeline para resumir o JUnit.
- `dados/`: bases geradas em CSV e JSON.
- `graficos/`: graficos gerados a partir das bases coletadas.
- `config/`: arquivos de configuracao usados para reproducao do experimento.

## Bases geradas

- `dados/pipeline_runs.csv`
- `dados/pipeline_metrics.csv`
- `dados/step_metrics.csv`
- `dados/pipeline_runs.json`

## Graficos gerados

- `graficos/workflow_duration_by_run.png`
- `graficos/job_duration_by_run.png`
- `graficos/status_rate.png`
- `graficos/tests_vs_duration.png`
- `graficos/average_step_duration.png`

## Reproducao resumida

```bash
python -m pip install -e ".[dev,analysis]"
python scripts/collect_metrics.py --repo Rafaelfurtadovs/ponderada_pipeline --workflow ci-metrics.yml --branch main --limit 20
python scripts/generate_charts.py --data-dir data --output-dir reports/figures
```

O relatorio tecnico contem a reproducao detalhada e a tabela com os IDs reais
das execucoes do GitHub Actions.
