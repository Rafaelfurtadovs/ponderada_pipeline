from __future__ import annotations

import argparse
import csv
import io
import json
import os
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

API_ROOT = "https://api.github.com"


@dataclass(frozen=True)
class GithubContext:
    repo: str
    token: str


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seconds_between(start: str | None, end: str | None) -> float:
    parsed_start = parse_datetime(start)
    parsed_end = parse_datetime(end)
    if not parsed_start or not parsed_end:
        return 0.0
    return round((parsed_end - parsed_start).total_seconds(), 2)


def get_token() -> str:
    env_token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if env_token:
        return env_token

    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("Defina GH_TOKEN/GITHUB_TOKEN ou autentique o GitHub CLI.") from exc

    return result.stdout.strip()


def request_json(context: GithubContext, path: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(
        f"{API_ROOT}{path}",
        headers={
            "Authorization": f"Bearer {context.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def request_bytes(context: GithubContext, url: str) -> bytes:
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {context.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.content


def collect_paginated(
    context: GithubContext,
    path: str,
    root_key: str,
    params: dict[str, Any] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1
    while True:
        query = {"per_page": 100, "page": page}
        if params:
            query.update(params)
        payload = request_json(context, path, query)
        page_items = payload[root_key]
        items.extend(page_items)
        if limit and len(items) >= limit:
            return items[:limit]
        if len(page_items) < 100:
            return items
        page += 1


def read_test_summary_from_artifacts(context: GithubContext, run_id: int) -> dict[str, Any]:
    artifacts = collect_paginated(
        context,
        f"/repos/{context.repo}/actions/runs/{run_id}/artifacts",
        "artifacts",
    )
    test_artifact = next(
        (artifact for artifact in artifacts if artifact["name"].startswith("test-results-")),
        None,
    )
    if not test_artifact:
        return {}

    archive = request_bytes(context, test_artifact["archive_download_url"])
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        if "experiment-summary.json" not in zipped.namelist():
            return {}
        with zipped.open("experiment-summary.json") as handle:
            return json.load(handle)


def normalize_status(conclusion: str | None) -> str:
    return conclusion or "in_progress"


def commit_message(run: dict[str, Any]) -> str:
    head_commit = run.get("head_commit") or {}
    message = head_commit.get("message") or run.get("display_title") or ""
    return message.splitlines()[0]


def run_url(repo: str, run_id: int) -> str:
    return f"https://github.com/{repo}/actions/runs/{run_id}"


def collect_metrics(
    context: GithubContext,
    workflow: str,
    branch: str,
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    runs = collect_paginated(
        context,
        f"/repos/{context.repo}/actions/workflows/{workflow}/runs",
        "workflow_runs",
        params={"branch": branch, "event": "push"},
        limit=limit,
    )

    run_rows: list[dict[str, Any]] = []
    job_rows: list[dict[str, Any]] = []
    step_rows: list[dict[str, Any]] = []

    for run in sorted(runs, key=lambda item: item["run_number"]):
        run_id = int(run["id"])
        summary = read_test_summary_from_artifacts(context, run_id)
        scenario = summary.get("scenario", {})
        test_count = int(summary.get("test_count", 0))
        test_failures = int(summary.get("test_failures", 0)) + int(summary.get("test_errors", 0))
        test_average_time = float(summary.get("test_average_time", 0.0))
        workflow_duration = seconds_between(run.get("run_started_at"), run.get("updated_at"))

        run_row = {
            "run_id": run_id,
            "run_number": run["run_number"],
            "run_url": run_url(context.repo, run_id),
            "commit_sha": run["head_sha"],
            "commit_short_sha": run["head_sha"][:7],
            "commit_message": commit_message(run),
            "status": normalize_status(run.get("conclusion")),
            "workflow_duration": workflow_duration,
            "test_count": test_count,
            "test_failures": test_failures,
            "test_average_time": test_average_time,
            "test_total_time": float(summary.get("test_time", 0.0)),
            "timestamp": run.get("run_started_at") or run.get("created_at"),
            "scenario_id": scenario.get("scenario_id", ""),
            "execution_mode": scenario.get("execution_mode", ""),
            "cache": scenario.get("cache", ""),
            "generated_test_count": scenario.get("generated_test_count", ""),
            "slow_test_delay_seconds": scenario.get("slow_test_delay_seconds", ""),
            "failing_case": scenario.get("failing_case", ""),
            "scenario_notes": scenario.get("notes", ""),
        }
        run_rows.append(run_row)

        jobs = collect_paginated(
            context,
            f"/repos/{context.repo}/actions/runs/{run_id}/jobs",
            "jobs",
        )
        for job in jobs:
            job_duration = seconds_between(job.get("started_at"), job.get("completed_at"))
            job_row = {
                **run_row,
                "job_name": job["name"],
                "job_status": normalize_status(job.get("conclusion")),
                "job_duration": job_duration,
            }
            job_rows.append(job_row)

            for step in job.get("steps", []):
                step_rows.append(
                    {
                        "run_id": run_id,
                        "run_number": run["run_number"],
                        "commit_sha": run["head_sha"],
                        "commit_message": commit_message(run),
                        "status": normalize_status(run.get("conclusion")),
                        "job_name": job["name"],
                        "step_name": step["name"],
                        "step_status": normalize_status(step.get("conclusion")),
                        "step_number": step["number"],
                        "step_started_at": step.get("started_at"),
                        "step_completed_at": step.get("completed_at"),
                        "step_duration": seconds_between(
                            step.get("started_at"),
                            step.get("completed_at"),
                        ),
                        "scenario_id": scenario.get("scenario_id", ""),
                        "execution_mode": scenario.get("execution_mode", ""),
                        "cache": scenario.get("cache", ""),
                    }
                )

    return run_rows, job_rows, step_rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "rows": rows,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta metricas reais do GitHub Actions.")
    parser.add_argument("--repo", required=True, help="Repositorio no formato owner/name.")
    parser.add_argument("--workflow", default="ci-metrics.yml", help="Nome ou arquivo do workflow.")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()

    context = GithubContext(repo=args.repo, token=get_token())
    run_rows, job_rows, step_rows = collect_metrics(context, args.workflow, args.branch, args.limit)

    if not run_rows:
        print("Nenhuma execucao encontrada para os filtros informados.", file=sys.stderr)
        sys.exit(1)

    write_csv(args.output_dir / "pipeline_runs.csv", run_rows)
    write_csv(args.output_dir / "pipeline_metrics.csv", job_rows)
    write_csv(args.output_dir / "step_metrics.csv", step_rows)
    write_json(args.output_dir / "pipeline_runs.json", run_rows)

    print(f"Coletadas {len(run_rows)} execucoes, {len(job_rows)} jobs e {len(step_rows)} etapas.")


if __name__ == "__main__":
    main()
