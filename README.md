# Experimento de metricas de pipeline CI/CD

Este repositorio contem um experimento pratico para medir execucoes reais de um
pipeline no GitHub Actions. O projeto usa uma biblioteca Python pequena com
testes automatizados e um workflow que executa:

- instalacao de dependencias;
- lint com Ruff;
- testes com Pytest;
- upload de artefatos com JUnit XML e resumo do cenario;
- coleta posterior de metricas pela API do GitHub.

## Estrutura

- `.github/workflows/ci-metrics.yml`: pipeline do experimento.
- `experiment_scenario.json`: parametros controlados de cada execucao.
- `src/pipeline_lab/`: codigo Python testado pelo pipeline.
- `tests/`: suite automatizada, parametrizada pelo cenario.
- `scripts/collect_metrics.py`: coleta metricas reais via API do GitHub.
- `scripts/generate_charts.py`: gera os graficos a partir dos CSVs.
- `scripts/set_scenario.py`: altera o cenario de forma reproduzivel.
- `reports/technical_report.md`: relatorio tecnico do experimento.

## Como reproduzir

1. Crie e ative um ambiente Python 3.12.
2. Instale as dependencias:

```bash
python -m pip install -e ".[dev,analysis]"
```

3. Execute lint e testes localmente:

```bash
ruff check .
pytest --junitxml=reports/junit.xml
```

4. Aplique variacoes no cenario e faca push para disparar o GitHub Actions:

```bash
python scripts/set_scenario.py --scenario-id baseline --mode parallel --cache enabled --tests 12 --delay 0 --fail none --notes "Baseline verde"
git add experiment_scenario.json
git commit -m "experiment baseline scenario"
git push
```

5. Depois das execucoes reais, colete as metricas:

```bash
python scripts/collect_metrics.py --repo Rafaelfurtadovs/ponderada_pipeline --workflow ci-metrics.yml --branch main --limit 20
```

6. Gere os graficos:

```bash
python scripts/generate_charts.py --data-dir data --output-dir reports/figures
```

Os arquivos `data/pipeline_metrics.csv`, `data/pipeline_runs.csv`,
`data/step_metrics.csv` e os graficos em `reports/figures/` sao derivados das
execucoes reais do GitHub Actions.
