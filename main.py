"""Startpunkt för orderrapporten."""

import logging
from order_report import OrderDataError, run_report


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        run_report()
    except (OrderDataError, OSError) as error:
        logging.getLogger(__name__).error("Rapporten kunde inte skapas: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
