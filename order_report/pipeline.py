"""Programmets sammanhållande flöde."""

from .config import ReportConfig
from .processing import OverviewSummary, add_order_values, clean_orders, summarize_orders
from .reporting import build_reports, save_reports
from .validation import load_orders


def run_report(config: ReportConfig | None = None) -> OverviewSummary:
    """Kör hela rapportflödet och returnera sammanfattningen."""
    config = config or ReportConfig()
    raw_orders = load_orders(config)
    orders = add_order_values(clean_orders(raw_orders))
    summary = summarize_orders(orders)
    save_reports(build_reports(orders, summary), config)
    return summary
