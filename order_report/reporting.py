"""Skapande och lagring av rapporter."""

import logging
from pathlib import Path
import pandas as pd

from .config import ReportConfig
from .processing import OverviewSummary

logger = logging.getLogger(__name__)


def build_overview(summary: OverviewSummary) -> pd.DataFrame:
    return pd.DataFrame({
        "metric": ["total_sales", "order_count", "return_count"],
        "value": [summary.total_sales, summary.order_count, summary.return_count],
    })


def build_sales_report(data: pd.DataFrame, group_column: str) -> pd.DataFrame:
    report = data.groupby(group_column, as_index=False).agg(
        order_count=("order_id", "nunique"),
        total_sales=("discounted_value", "sum"),
        returns=("returned", "sum"),
    )
    report["total_sales"] = report["total_sales"].round(2)
    report["return_rate"] = (report["returns"] / report["order_count"]).round(3)
    return report.sort_values("total_sales", ascending=False).reset_index(drop=True)


def build_returns_report(data: pd.DataFrame, group_column: str) -> pd.DataFrame:
    report = data.groupby(group_column, as_index=False).agg(
        order_count=("order_id", "nunique"), returns=("returned", "sum")
    )
    report["return_rate"] = (report["returns"] / report["order_count"]).round(3)
    return report.sort_values("return_rate", ascending=False).reset_index(drop=True)


def build_reports(data: pd.DataFrame, summary: OverviewSummary) -> dict[str, pd.DataFrame]:
    reports = {
        "overview.csv": build_overview(summary),
        "sales_by_category.csv": build_sales_report(data, "product_category"),
        "sales_by_region.csv": build_sales_report(data, "region"),
        "returns_by_category.csv": build_returns_report(data, "product_category"),
    }
    logger.info("Skapade %d rapporter", len(reports))
    return reports


def save_reports(reports: dict[str, pd.DataFrame], config: ReportConfig) -> list[Path]:
    config.output_folder.mkdir(parents=True, exist_ok=True)
    saved = []
    for filename, report in reports.items():
        path = config.output_path(filename)
        report.to_csv(path, index=False)
        saved.append(path)
        logger.info("Sparade %s", path)
    return saved
