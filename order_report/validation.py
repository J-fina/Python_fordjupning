"""Inläsning och validering av orderdata."""

import logging
import pandas as pd

from .config import ReportConfig

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = (
    "order_id", "order_date", "customer_id", "region", "product_category",
    "quantity", "unit_price", "discount", "returned",
)


class OrderDataError(Exception):
    """Fel som beror på att indatan inte går att använda."""


def validate_orders(data: pd.DataFrame) -> None:
    """Kontrollera obligatoriska kolumner och att datan inte är tom."""
    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise OrderDataError(
            "Följande obligatoriska kolumner saknas: " + ", ".join(missing)
        )
    if data.empty:
        raise OrderDataError("Datasetet innehåller inga rader")
    logger.info("Validering klar")


def load_orders(config: ReportConfig) -> pd.DataFrame:
    """Läs CSV-filen och validera innehållet."""
    if not config.input_file.is_file():
        raise OrderDataError(f"Hittar ingen datafil: {config.input_file}")
    logger.info("Läser data från %s", config.input_file)
    try:
        data = pd.read_csv(config.input_file)
    except pd.errors.EmptyDataError as error:
        raise OrderDataError(f"Datafilen är tom: {config.input_file}") from error
    except pd.errors.ParserError as error:
        raise OrderDataError(f"CSV-filen kunde inte tolkas: {error}") from error
    logger.info("Läste in %d rader", len(data))
    validate_orders(data)
    return data
