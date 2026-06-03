from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def configure_style() -> None:
    plt.rcParams.update(
        {
            "figure.figsize": (11, 6),
            "axes.grid": True,
            "grid.alpha": 0.25,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 10,
        }
    )


def save_workflow_duration(runs: pd.DataFrame, output_dir: Path) -> None:
    ordered = runs.sort_values("run_number")
    colors = ordered["status"].map({"success": "#2e7d59", "failure": "#c44536"}).fillna("#667085")

    fig, ax = plt.subplots()
    ax.bar(ordered["run_number"].astype(str), ordered["workflow_duration"], color=colors)
    ax.set_title("Tempo total do workflow por execucao")
    ax.set_xlabel("Numero da execucao")
    ax.set_ylabel("Duracao total (s)")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(output_dir / "workflow_duration_by_run.png", dpi=160)
    plt.close(fig)


def save_job_duration(jobs: pd.DataFrame, output_dir: Path) -> None:
    filtered = jobs[jobs["job_duration"] > 0].copy()
    pivot = filtered.pivot_table(
        index="run_number",
        columns="job_name",
        values="job_duration",
        aggfunc="sum",
        fill_value=0,
    ).sort_index()

    fig, ax = plt.subplots()
    pivot.plot(kind="bar", stacked=True, ax=ax, colormap="tab20")
    ax.set_title("Tempo por job em cada execucao")
    ax.set_xlabel("Numero da execucao")
    ax.set_ylabel("Duracao do job (s)")
    ax.legend(title="Job", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(output_dir / "job_duration_by_run.png", dpi=160)
    plt.close(fig)


def save_status_rate(runs: pd.DataFrame, output_dir: Path) -> None:
    counts = runs["status"].value_counts().reindex(["success", "failure"], fill_value=0)
    total = counts.sum()
    rates = counts / total * 100 if total else counts

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(rates.index, rates.values, color=["#2e7d59", "#c44536"])
    ax.set_title("Taxa de sucesso e falha")
    ax.set_xlabel("Status")
    ax.set_ylabel("Percentual das execucoes (%)")
    ax.set_ylim(0, 100)
    for index, value in enumerate(rates.values):
        ax.text(index, value + 2, f"{value:.1f}%", ha="center")
    fig.tight_layout()
    fig.savefig(output_dir / "status_rate.png", dpi=160)
    plt.close(fig)


def save_tests_vs_duration(runs: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots()
    for status, group in runs.groupby("status"):
        ax.scatter(
            group["test_count"],
            group["workflow_duration"],
            s=80,
            label=status,
            alpha=0.85,
        )
    ax.set_title("Relacao entre quantidade de testes e duracao do pipeline")
    ax.set_xlabel("Quantidade de testes")
    ax.set_ylabel("Duracao total do workflow (s)")
    ax.legend(title="Status")
    fig.tight_layout()
    fig.savefig(output_dir / "tests_vs_duration.png", dpi=160)
    plt.close(fig)


def save_step_duration(steps: pd.DataFrame, output_dir: Path) -> None:
    relevant = steps[
        steps["step_name"].isin(["Set up Python", "Install dependencies", "Run Ruff", "Run Pytest"])
    ].copy()
    grouped = (
        relevant.groupby(["step_name"], as_index=False)["step_duration"]
        .mean()
        .sort_values("step_duration", ascending=False)
    )

    fig, ax = plt.subplots()
    ax.barh(grouped["step_name"], grouped["step_duration"], color="#4b6f8f")
    ax.set_title("Duracao media das etapas relevantes")
    ax.set_xlabel("Duracao media (s)")
    ax.set_ylabel("Etapa")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(output_dir / "average_step_duration.png", dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera graficos das metricas coletadas.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/figures"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    configure_style()

    runs = pd.read_csv(args.data_dir / "pipeline_runs.csv")
    jobs = pd.read_csv(args.data_dir / "pipeline_metrics.csv")
    steps = pd.read_csv(args.data_dir / "step_metrics.csv")

    save_workflow_duration(runs, args.output_dir)
    save_job_duration(jobs, args.output_dir)
    save_status_rate(runs, args.output_dir)
    save_tests_vs_duration(runs, args.output_dir)
    save_step_duration(steps, args.output_dir)

    print(f"Graficos gerados em {args.output_dir}")


if __name__ == "__main__":
    main()
