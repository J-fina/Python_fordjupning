"""Tvätt och beräkningar för orderdata."""

import logging
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)
TRUE_VALUES = ("true", "yes", "1", "ja")


@dataclass(frozen=True)
class OverviewSummary:
    total_sales: float
    order_count: int
    return_count: int


def _to_numeric(series: pd.Series, column: str) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    invalid_count = int(numeric.isna().sum())
    if invalid_count:
        logger.warning("%s har %d saknade eller ogiltiga värden", column, invalid_count)
    return numeric


def clean_orders(data: pd.DataFrame) -> pd.DataFrame:
    """Tvätta datan utan att ändra den inkommande DataFrame-objektet."""
    cleaned = data.copy()
    for column in ("region", "product_category"):
        cleaned[column] = cleaned[column].fillna("Unknown").astype(str).str.strip().str.title()

    cleaned["quantity"] = _to_numeric(cleaned["quantity"], "quantity").fillna(1)
    cleaned["discount"] = _to_numeric(cleaned["discount"], "discount").fillna(0)

    prices = _to_numeric(cleaned["unit_price"], "unit_price")
    if not prices.notna().any():
        logger.warning("unit_price saknar helt giltiga tal")
    else:
        median_price = prices.median()
        prices = prices.fillna(median_price)
    cleaned["unit_price"] = prices
    cleaned["returned"] = cleaned["returned"].astype(str).str.strip().str.lower().isin(TRUE_VALUES)

    unreasonable = (
        (cleaned["quantity"] <= 0)
        | (cleaned["unit_price"] < 0)
        | ~cleaned["discount"].between(0, 1)
    )
    if unreasonable.any():
        logger.warning("%d rader har orimliga numeriska värden", int(unreasonable.sum()))
    return cleaned


def add_order_values(data: pd.DataFrame) -> pd.DataFrame:
    """Lägg till ordervärde före och efter rabatt."""
    result = data.copy()
    result["order_value"] = result["quantity"] * result["unit_price"]
    result["discounted_value"] = result["order_value"] * (1 - result["discount"])
    return result


def summarize_orders(data: pd.DataFrame) -> OverviewSummary:
    """Räkna totalsumma, unika orders och returer."""
    return OverviewSummary(
        total_sales=round(data["discounted_value"].sum(), 2),
        order_count=int(data["order_id"].nunique()),
        return_count=int(data["returned"].sum()),
    )
